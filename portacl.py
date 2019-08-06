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

docker_client = None
docker_event_slots = {}


def docker_event_slot(event_type, action):
    """Decorator for docker slot.

    A docker slot is a function that takes a docker event (in dict form) as
    argument, and is decorated by this decorator. It is registered in the
    docker_event_slot dictionary, and looked up in docker_listen upon receiving
    a docker event. See
    https://docs.docker.com/engine/reference/commandline/events/.

    For example:

    @docker_event_slot("container", "create")
    def my_docker_slot(event):
        ...

    function my_docker_slot will be called whenever a container create event is
    received.
    """
    def decorator(slot):
        global docker_event_slots
        docker_event_slots[event_type + "_" + action] = slot
        return slot
    return decorator


def static_var(variable_name, initial_value):
    """Decorator that assigns a static variable to the decorated function.

    Credits: Claudiu https://stackoverflow.com/questions/279561/what-is-the-python-equivalent-of-static-variables-inside-a-function
    """
    def decorator(func):
        setattr(func, variable_name, initial_value)
        return func
    return decorator


def docker_listen():
    """Main loop.

    This function listen for docker events indefinitely, and calls docker slots
    registered using the docker_event_slot decorator.

    Raises:
        docker.errors.APIError: If the docker server returned an error.
    """
    logging.info("Entering event loop")
    for event in docker_client.events(decode=True):
        event_type = event.get("Type")
        action = event.get("Action")
        slot = docker_event_slots.get(event_type + "_" + action, None)
        if slot:
            logging.debug("Received supported docker event " + str(event))
            slot(event)


def load_env():
    """Reads relevent environment variables."""
    def import_env_var(name, default=""):
        globals()[name] = os.environ.get(name, default)
    import_env_var("DOCKER_CERT_PATH")
    import_env_var("DOCKER_HOST", "unix:///var/run/docker.sock")
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
    logging.info("Connecting to docker host {}".format(DOCKER_HOST))
    global docker_client
    docker_client = docker.from_env()
    docker_listen()


@docker_event_slot("container", "create")
def on_container_create(event):
    """Slot called when a container is created.
    """
    actor = event.get("Actor")
    attributes = actor.get("Attributes")
    portainer_set_uac(
        public=attributes.get("io.portainer.uac.public", ""),
        ressource_id=actor["ID"],
        ressource_type="container",
        teams=attributes.get("io.portainer.uac.teams", ""),
        users=attributes.get("io.portainer.uac.users", "")
    )


@docker_event_slot("volume", "create")
def on_volume_create(event):
    volume = docker_client.volumes.get(event.get("Actor").get("ID"))
    labels = volume.attrs.get("Labels", {})
    portainer_set_uac(
        public=labels.get("io.portainer.uac.public", ""),
        ressource_id=volume.id,
        ressource_type="volume",
        teams=labels.get("io.portainer.uac.teams", ""),
        users=labels.get("io.portainer.uac.users", "")
    )


@static_var("token", None)
def portainer_request(method, url, json={}):
    """Issues an API request to the portainer endpoint.

    (Re)authenticates if necessary. This is just a convenient wrapper.
    Portainer API reference:
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
    def authenticate():
        logging.info("Authenticating to portainer api {}"
                     .format(PORTAINER_API_URL))
        r = requests.post(PORTAINER_API_URL + "/auth", json={
            "Password": PORTAINER_API_PASSWORD,
            "Username": PORTAINER_API_USERNAME
        })
        r.raise_for_status()
        portainer_request.token = r.json()["jwt"]

    def issue_request():
        f = {
            "DELETE": requests.delete,
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put
        }[method]
        authorization_header = {
            "Authorization": "Bearer " + portainer_request.token
        } if portainer_request.token is not None else None
        r = f(PORTAINER_API_URL + url, json=json, headers=authorization_header)
        r.raise_for_status()
        return r.json()

    try:
        return issue_request()
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            authenticate()
            return issue_request()
        else:
            raise e


@static_var("uac", {})
def portainer_set_uac(**kwargs):
    """Updates the uac of a docker ressource.

    Args:
        public (str): Raw value of label io.portainer.uac.public.
        ressource_id (int): Docker ressource id.
        ressource_type (str): Docker ressource type (container, volume, etc.).
        subressource_ids (List[int]): Docker subressource ids.
        teams (str): Raw value of label io.portainer.uac.teams.
        users (str): Raw value of label io.portainer.uac.users.
    """
    ressource_id = kwargs.get("ressource_id")
    ressource_type = kwargs.get("ressource_type")
    if ressource_id is None:
        raise ValueError("UAC must specify a docker ressource id.")
    elif ressource_type is None:
        raise ValueError("UAC must specify a docker ressource type.")
    public = (kwargs.get("public").lower() == "true")
    subressource_ids = kwargs.get("subressource_ids", [])
    teams = [] if kwargs.get("teams") in [None, ""] else \
        [team_id(x.strip()) for x in str(kwargs.get("teams")).split(',')]
    users = [] if kwargs.get("users") in [None, ""] else \
        [user_id(x.strip()) for x in str(kwargs.get("users")).split(',')]
    if not public and len(teams) == 0 and len(users) == 0:
        logging.warning(f'ACL for ressource {ressource_id} is empty, skipping')
    else:
        if ressource_id in portainer_set_uac.uac:
            current_public = portainer_set_uac.uac["io.portainer.uac.public"]
            current_subressource_ids = \
                portainer_set_uac.uac["io.portainer.subressources"]
            current_teams = portainer_set_uac.uac["io.portainer.uac.teams"]
            current_users = portainer_set_uac.uac["io.portainer.uac.users"]
            new_public = current_public or public
            new_subressource_ids = list(set(
                current_subressource_ids + subressource_ids))
            new_teams = list(set(current_teams + teams))
            new_users = list(set(current_users + users))
            try:
                portainer_request(
                    "PUT",
                    "/resource_controls/" + ressource_id,
                    {
                        "Public": new_public,
                        "SubResourceIDs": new_subressource_ids,
                        "Teams": new_teams,
                        "Users": new_users
                    })
                portainer_set_uac.uac[ressource_id] = {
                    "io.portainer.uac.public": new_public,
                    "io.portainer.subressources": new_subressource_ids,
                    "io.portainer.uac.teams": new_teams,
                    "io.portainer.uac.users": new_users
                }
            except requests.HTTPError:
                logging.error(
                    f'Could not update ACL of {ressource_id}: {str(e)}')
        else:
            try:
                portainer_request(
                    "DELETE", "/resource_controls/" + ressource_id)
            except requests.HTTPError:
                pass
            try:
                portainer_request("POST", "/resource_controls", {
                    "Public": public,
                    "ResourceID": ressource_id,
                    "SubResourceIDs": subressource_ids,
                    "Teams": teams,
                    "Type": ressource_type,
                    "Users": users
                })
                portainer_set_uac.uac[ressource_id] = {
                    "io.portainer.uac.public": public,
                    "io.portainer.subressources": subressource_ids,
                    "io.portainer.uac.teams": teams,
                    "io.portainer.uac.users": users
                }
            except requests.HTTPError as e:
                logging.error(
                    f'Could not create new ACL for {ressource_id}: {str(e)}')


@static_var("teams", {})
def team_id(name):
    """Gets the id of a team.

    Teamnames are assumed not to start with a digit. If a valid team id is
    passed in string format, then that id is returned (this simplifies some
    code).

    Returns:
        Id of the team as an int.
    """
    if name not in team_id.teams:
        for team in portainer_request("GET", "/teams"):
            team_id.teams[team["Name"]] = int(team["Id"])
            team_id.teams[str(team["Id"])] = int(team["Id"])
    if name not in team_id.teams:
        raise ValueError(f'Team "{name}" not known by portainer')
    return team_id.teams[name]


@static_var("users", {})
def user_id(name):
    """Gets the id of a user.

    Usernames are assumed not to start with a digit. If a valid user id is
    passed in string format, then that id is returned (this simplifies some
    code).

    Returns:
        Id of the user as an int.
    """
    if name not in user_id.users:
        for user in portainer_request("GET", "/users"):
            user_id.users[user["Username"]] = int(user["Id"])
            user_id.users[str(user["Id"])] = int(user["Id"])
    if name not in user_id.users:
        raise ValueError(f'User "{name}" not known by portainer')
    return user_id.users[name]


if __name__ == "__main__":
    main()
