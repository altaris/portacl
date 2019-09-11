"""Main (and only) module.
"""

import logging
import os
import requests

import docker


DOCKER_CERT_PATH = ""
DOCKER_HOST = ""
DOCKER_TLS_VERIFY = ""
LOGGING_LEVEL = ""
PORTAINER_API_PASSWORD = ""
PORTAINER_API_USERNAME = ""
PORTAINER_API_URL = ""


PORTAINER_ACLS = {}
DOCKER_CLIENT = None
DOCKER_EVENT_SLOTS = {}


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
        global DOCKER_EVENT_SLOTS  # pylint: disable=global-statement
        DOCKER_EVENT_SLOTS[event_type + "_" + action] = slot
        return slot
    return decorator


def static_var(variable_name, initial_value):
    # pylint: disable=line-too-long
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
    for event in DOCKER_CLIENT.events(decode=True):
        event_type = event.get("Type")
        action = event.get("Action")
        slot = DOCKER_EVENT_SLOTS.get(event_type + "_" + action, None)
        if slot:
            logging.debug("Received supported docker event %s", str(event))
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
    logging.info("Connecting to docker host %s", DOCKER_HOST)
    global DOCKER_CLIENT  # pylint: disable=global-statement
    DOCKER_CLIENT = docker.from_env()
    docker_listen()


@docker_event_slot("container", "create")
def on_container_create(event):
    """Slot called when a container is created.
    """
    actor = event.get("Actor")
    attributes = actor.get("Attributes")
    portainer_update_acl(
        public=attributes.get("io.portainer.uac.public", ""),
        resource_id=actor["ID"],
        resource_type="container",
        teams=attributes.get("io.portainer.uac.teams", ""),
        users=attributes.get("io.portainer.uac.users", "")
    )


@docker_event_slot("volume", "create")
def on_volume_create(event):
    """Slot called when a volume is created.
    """
    volume = DOCKER_CLIENT.volumes.get(event.get("Actor").get("ID"))
    labels = volume.attrs.get("Labels")
    if labels is None:
        labels = {}
    portainer_update_acl(
        public=labels.get("io.portainer.uac.public", ""),
        resource_id=volume.id,
        resource_type="volume",
        teams=labels.get("io.portainer.uac.teams", ""),
        users=labels.get("io.portainer.uac.users", "")
    )


# @docker_event_slot("volume", "mount")
def on_volume_mount(event):
    """This slot is called when a volume is mounted to a container.

    It makes the volume inherit the ACL of the container it is mounted to.
    Because of the limitations of the portainer API (specifically, the
    ResourceControlUpdateRequest model would need to include a SubResourceIDs
    field...), this slot does not take advantage of inherited ACLs mechanism.
    """
    volume_id = event["Actor"]["ID"]
    container_id = event["Actor"]["Attributes"]["container"]
    container_acl = PORTAINER_ACLS.get(container_id, {})
    container_public = container_acl.get("io.portainer.uac.public", False)
    container_teams = container_acl.get("io.portainer.uac.teams", [])
    container_users = container_acl.get("io.portainer.uac.users", [])
    portainer_update_acl(
        public=container_public,
        resource_id=volume_id,
        teams=container_teams,
        users=container_users
    )


@static_var("token", None)
def portainer_request(method, url, json=None):
    """Issues an API request to the portainer endpoint.

    (Re)authenticates if necessary. This is just a convenient wrapper.
    Portainer API reference:
    https://app.swaggerhub.com/apis/deviantony/Portainer/1.22.0/

    Args:
        method: Either "DELETE", "GET", "POST", or "PUT".
        url: The API method to call.
        json: The JSON data as a dict.

    Returns:
        The JSON response as a dict.

    Raises:
        requests.HTTPError: If an error occured.
    """
    if portainer_request.token is None:
        logging.info("Authenticating to portainer api %s", PORTAINER_API_URL)
        auth_r = requests.post(PORTAINER_API_URL + "/auth", json={
            "Password": PORTAINER_API_PASSWORD,
            "Username": PORTAINER_API_USERNAME
        })
        auth_r.raise_for_status()
        portainer_request.token = auth_r.json()["jwt"]
    logging.debug("%s %s %s: %s", PORTAINER_API_URL, url, method, str(json))
    method = {
        "DELETE": requests.delete,
        "GET": requests.get,
        "POST": requests.post,
        "PUT": requests.put
    }[method]
    authorization_header = {
        "Authorization": "Bearer " + portainer_request.token
    } if portainer_request.token is not None else None
    response = method(
        PORTAINER_API_URL + url,
        json=json,
        headers=authorization_header
    )
    response.raise_for_status()
    return response.json()


def portainer_update_acl(**kwargs):
    """Updates the acl of a docker resource.

    If an ACL for the resource already exists, it is merged with the new ACL.
    This means the following:
    * the resource is public if it already is OR if the new ACL mandates it;
    * a user (resp. team) is authorized if it already is or if the new ACL
      mandates it;
    * a docker resource is a subresource if it already is or if or if the new
      ACL mandates it.

    Args:
        public (str / bool): Raw value of label io.portainer.uac.public.
        resource_id (int): Docker resource id.
        resource_type (str): Docker resource type (container, volume, etc.).
        subresource_ids (List[int]): Docker subresource ids.
        teams (str / Table[int]): Raw or formatted value of label
                                  io.portainer.uac.teams.
        users (str / Table[int]): Raw or formatted value of label
                                  io.portainer.uac.users.
    """
    global PORTAINER_ACLS  # pylint: disable=global-statement

    def bool_or_str_to_bool(val):
        return val if isinstance(val, bool) else (str(val).lower() == "true")

    def idlist_or_str_to_idlist(val, str_to_id_func):
        return val if isinstance(val, list) else \
            [] if val in [None, ""] else \
            [str_to_id_func(x.strip()) for x in str(val).split(',')]

    # Extract and parse data from the kwargs
    resource_id = kwargs.get("resource_id")
    if resource_id is None:
        raise ValueError("ACL must specify a docker resource id.")
    resource_type = kwargs.get("resource_type")
    subresource_ids = kwargs.get("subresource_ids", [])
    public = bool_or_str_to_bool(kwargs.get("public"))
    teams = idlist_or_str_to_idlist(kwargs.get("teams"), team_id)
    users = idlist_or_str_to_idlist(kwargs.get("users"), user_id)

    # Check for trivial acl
    if not public and not subresource_ids and not teams and not users:
        logging.warning("ACL for resource %s is empty, skipping", resource_id)
        return
    else:
        logging.debug(
            "Updating ACL of resource %s (%s):"
            "io.portainer.uac.public |= %s, "
            "subresource_ids += %s, "
            "io.portainer.uac.teams += %s, "
            "io.portainer.uac.users += %s",
            resource_id, resource_type, public, subresource_ids, teams, users
        )

    # Fetch existing data and compute the new acl
    acl = PORTAINER_ACLS.get(resource_id, {})
    resource_control_id = acl.get("resource_control_id", None)
    acl_exists = (resource_control_id is not None)
    new_public = (acl.get("io.portainer.uac.public", False) or public)
    new_teams = list(set(acl.get("io.portainer.uac.teams", []) + teams))
    new_users = list(set(acl.get("io.portainer.uac.users", []) + users))
    new_subresource_ids = acl.get("subresource_ids", []) if acl_exists else \
        subresource_ids

    # Execute API request
    request_method = "PUT" if acl_exists else "POST"
    request_path = "/" + str(resource_control_id) if acl_exists else ""
    request_data = {
        "Public": new_public,
        "Teams": new_teams,
        "Users": new_users
    } if acl_exists else {
        "Public": new_public,
        "ResourceID": resource_id,
        "SubResourceIDs": new_subresource_ids,
        "Teams": new_teams,
        "Type": resource_type,
        "Users": new_users
    }
    try:
        response = portainer_request(
            request_method,
            "/resource_controls" + request_path,
            request_data)
        PORTAINER_ACLS[resource_id] = {
            "io.portainer.uac.public": new_public,
            "io.portainer.uac.teams": new_teams,
            "io.portainer.uac.users": new_users,
            "resource_control_id": response["Id"],
            "subresource_ids": new_subresource_ids
        }
        logging.info(
            "Updated ACL for resource %s (%s).", resource_id, resource_type
        )
    except requests.HTTPError as err:
        logging.error("Could not update ACL of %s: %s", resource_id, str(err))


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
