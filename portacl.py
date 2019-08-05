import docker
import logging
import os
import requests
import sys

DOCKER_CERT_PATH = ""
DOCKER_HOST = ""
DOCKER_TLS_VERIFY = ""
LOGGING_LEVEL = ""
PORTAINER_API_PASSWORD = ""
PORTAINER_API_USERNAME = ""
PORTAINER_API_URL = ""

docker_event_slots = {}
portainer_teams = {}
portainer_token = None
portainer_users = {}


def docker_event_slot(event_type, action):
    """Decorator for docker slot.

    A docker slot is a function that is decorated by this decorator. Is is
    registered in the docker_event_slot dictionary, and looked up in
    docker_listen upon receiving a docker event. See
    https://docs.docker.com/engine/reference/commandline/events/.

    For example:

    @docker_event_slot("container", "create")
    def my_docker_slot(**kwargs):
        ...

    function my_docker_slot will be called whenever a container create event is
    received.
    """
    def decorator(slot):
        global docker_event_slots
        docker_event_slots[event_type + "_" + action] = slot
        return slot
    return decorator


def docker_listen():
    """Main loop.

    This function listen for docker events indefinitely, and calls docker slots
    registered using the docker_event_slot decorator.

    Raises:
        docker.errors.APIError: If the docker server returned an error.
    """
    logging.info("Connecting to docker host {}".format(DOCKER_HOST))
    docker_client = docker.from_env()
    logging.info("Entering event loop")
    for event in docker_client.events(decode=True):
        logging.debug("Received docker event " + str(event))
        event_type = event.get("Type")
        action = event.get("Action")
        slot = docker_event_slots.get(event_type + "_" + action, None)
        if slot:
            actor = event.get("Actor")
            attributes = actor.get("Attributes")
            raw_teams = attributes.get("io.portainer.uac.teams")
            raw_users = attributes.get("io.portainer.uac.users")
            public = (
                str(attributes.get("io.portainer.uac.public")).lower() ==
                "true"
            )
            teams = [] if raw_teams is None else \
                [team_id(x.strip()) for x in str(raw_teams).split(',')]
            users = [] if raw_users is None else \
                [user_id(x.strip()) for x in str(raw_users).split(',')]
            slot(
                action=action,
                id=actor.get("ID", "?" * 12),
                io_portainer_uac_public=public,
                io_portainer_uac_teams=teams,
                io_portainer_uac_users=users,
                name=attributes.get("name", "<no_name>"),
                event_type=event_type
            )


def load_env():
    """Reads relevent environment variables."""
    def import_env_var(name, default=""):
        globals()[name] = os.environ.get(name, default)
    import_env_var("DOCKER_CERT_PATH")
    import_env_var("DOCKER_HOST", "unix://var/run/docker.sock")
    import_env_var("DOCKER_TLS_VERIFY")
    import_env_var("LOGGING_LEVEL", "WARNING")
    import_env_var("PORTAINER_API_PASSWORD")
    import_env_var("PORTAINER_API_USERNAME")
    import_env_var("PORTAINER_API_URL")


def main():
    """The main function."""
    load_env()
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level={
            "CRITICAL": logging.CRITICAL,
            "DEBUG": logging.DEBUG,
            "ERROR": logging.ERROR,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING
        }[LOGGING_LEVEL])
    portainer_init()
    docker_listen()


# @docker_event_slot("config", "create")
@docker_event_slot("container", "create")
# @docker_event_slot("secret", "create")
# @docker_event_slot("service", "create")
# @docker_event_slot("stack", "create")
# @docker_event_slot("volume", "create")
def on_something_create(**kwargs):
    """Slot called when something is created.

    Currently only supports container creations.
    """
    logging.info("Setting ACL for {type} {id} ({name}): {acl}".format(
        acl=str({
            "io.portainer.uac.public": kwargs["io_portainer_uac_public"],
            "io.portainer.uac.teams": kwargs["io_portainer_uac_teams"],
            "io.portainer.uac.users": kwargs["io_portainer_uac_users"]
        }),
        id=kwargs["id"][:12],
        name=kwargs["name"],
        type=kwargs["event_type"]
    ))
    portainer_request("POST", "/resource_controls", {
        "Public": kwargs["io_portainer_uac_public"],
        "ResourceID": kwargs["id"],
        "SubResourceIDs": [],
        "Teams": kwargs["io_portainer_uac_teams"],
        "Type": kwargs["event_type"],
        "Users": kwargs["io_portainer_uac_users"]
    })


def portainer_init():
    """Connects to the portainer API and stores relevant data.

    TODO: Load user and team data each time they are needed.
    """
    logging.info("Authenticating to portainer api {}"
                 .format(PORTAINER_API_URL))
    global portainer_token
    portainer_token = portainer_request("POST", "/auth", {
        "Password": PORTAINER_API_PASSWORD,
        "Username": PORTAINER_API_USERNAME
    })["jwt"]


def portainer_request(method, url, json={}):
    """Issues an API request to the portainer endpoint.

    This is just a convenient wrapper. Portainer API reference:
    https://app.swaggerhub.com/apis/deviantony/Portainer/1.22.0/

    Args:
        method: Either "DELETE", "GET", "POST", or "PUT".
        url: The API method to call, e.g. "/auth".
        json: The JSON data as a dict.

    Returns:
        The JSON response as a dict.

    Raises:
        requests.HTTPError: If an error occured.
    """
    logging.debug(url + " " + method + " " + str(json))
    f = {
        "DELETE": requests.delete,
        "GET": requests.get,
        "POST": requests.post,
        "PUT": requests.put
    }[method]
    authorization_header = {
        "Authorization": "Bearer " + portainer_token
    } if portainer_token is not None else None
    r = f(PORTAINER_API_URL + url, json=json, headers=authorization_header)
    r.raise_for_status()
    return r.json()


def team_id(name):
    """Gets the id of a team.

    Teamnames are assumed not to start with a digit. If a valid team id is
    passed in string format, then that id is returned (this simplifies some
    code).
    """
    if name not in portainer_teams:
        for team in portainer_request("GET", "/teams"):
            portainer_teams[team["Name"]] = int(team["Id"])
            portainer_teams[str(team["Id"])] = int(team["Id"])
    if name not in portainer_teams:
        raise ValueError(f'Team "{name}" not known by portainer')
    return portainer_teams[name]


def user_id(name):
    """Gets the id of a user.

    Usernames are assumed not to start with a digit. If a valid user id is
    passed in string format, then that id is returned (this simplifies some
    code).
    """
    if name not in portainer_users:
        for user in portainer_request("GET", "/users"):
            portainer_users[user["Username"]] = int(user["Id"])
            portainer_users[str(user["Id"])] = int(user["Id"])
    if name not in portainer_users:
        raise ValueError(f'User "{name}" not known by portainer')
    return portainer_users[name]


if __name__ == "__main__":
    main()
