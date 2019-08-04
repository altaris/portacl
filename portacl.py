import docker
import logging
import os
import requests

DOCKER_CERT_PATH       = os.environ.get("DOCKER_CERT_PATH", "")
DOCKER_HOST            = os.environ.get("DOCKER_HOST", "")
DOCKER_TLS_VERIFY      = os.environ.get("DOCKER_TLS_VERIFY", "")
LOGGING_LEVEL          = os.environ.get("LOGGING_LEVEL", "WARNING")
PORTAINER_API_PASSWORD = os.environ.get("PORTAINER_API_PASSWORD", "")
PORTAINER_API_USERNAME = os.environ.get("PORTAINER_API_USERNAME", "")
PORTAINER_API_URL      = os.environ.get("PORTAINER_API_URL", "")

portainer_teams = {}
portainer_token = None
portainer_users = {}


def apply_acl(**kwargs):
    logging.info("Setting acl for container {id} ({name}): {acl}".format(
        id=kwargs["id"][:12],
        name=kwargs["name"],
        acl=str({
            "io.portainer.uac.public": kwargs["io_portainer_uac_public"],
            "io.portainer.uac.teams": kwargs["io_portainer_uac_teams"],
            "io.portainer.uac.users": kwargs["io_portainer_uac_users"]
        })
    ))
    portainer_request("POST", "/resource_controls", {
        "Public": kwargs["io_portainer_uac_public"],
        "ResourceID": kwargs["id"],
        "SubResourceIDs": [],
        "Teams": kwargs["io_portainer_uac_teams"],
        "Type": "container",
        "Users": kwargs["io_portainer_uac_users"]
    })


def docker_listen():
    logging.info("Connecting to docker host {}".format(DOCKER_HOST))
    docker_client = docker.from_env()
    logging.info("Entering event loop")
    for event in docker_client.events(decode=True):
        if event.get("Type") == "container" and event.get("Action") == "create":
            ac = event.get("Actor")
            at = ac.get("Attributes")
            raw_teams = at.get("io.portainer.uac.teams")
            raw_users = at.get("io.portainer.uac.users")
            public = (str(at.get("io.portainer.uac.public")).lower() == "true")
            teams = [] if raw_teams is None else \
                [portainer_teams[x.strip()] for x in str(raw_teams).split(',')]
            users = [] if raw_users is None else \
                [portainer_users[x.strip()] for x in str(raw_users).split(',')]
            apply_acl(
                id=ac.get("ID", "?" * 12),
                io_portainer_uac_public=public,
                io_portainer_uac_teams=teams,
                io_portainer_uac_users=users,
                name=at.get("name", "<no_name>")
            )


def load_env():
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level={
            "CRITICAL": logging.CRITICAL,
            "DEBUG":    logging.DEBUG,
            "ERROR":    logging.ERROR,
            "INFO":     logging.INFO,
            "WARNING":  logging.WARNING
        }[LOGGING_LEVEL])
    logging.debug("DOCKER_CERT_PATH = \"{}\""
        .format(DOCKER_CERT_PATH))
    logging.debug("DOCKER_HOST = \"{}\""
        .format(DOCKER_HOST))
    logging.debug("DOCKER_TLS_VERIFY = \"{}\""
        .format(DOCKER_TLS_VERIFY))
    logging.debug("LOGGING_LEVEL = \"{}\""
        .format(LOGGING_LEVEL))
    logging.debug("PORTAINER_API_PASSWORD = \"{}\""
        .format(PORTAINER_API_PASSWORD))
    logging.debug("PORTAINER_API_USERNAME = \"{}\""
        .format(PORTAINER_API_USERNAME))
    logging.debug("PORTAINER_API_URL = \"{}\""
        .format(PORTAINER_API_URL))


def portainer_init():
    """
    Reference: https://app.swaggerhub.com/apis/deviantony/Portainer/1.22.0/#/auth/AuthenticateUser
    """
    logging.info("Authenticating to portainer api {}".format(PORTAINER_API_URL))
    r = requests.post(PORTAINER_API_URL + "/auth",
        json={
            "Password": PORTAINER_API_PASSWORD,
            "Username": PORTAINER_API_USERNAME
    })
    r.raise_for_status()
    global portainer_token
    portainer_token = r.json()["jwt"]
    for user in portainer_request("GET", "/users"):
        portainer_users[user["Username"]] = int(user["Id"])
        portainer_users[str(user["Id"])] = int(user["Id"])
    logging.debug("Portainer users: " + str(portainer_users))
    for team in portainer_request("GET", "/teams"):
        portainer_teams[team["Name"]] = int(team["Id"])
        portainer_teams[str(team["Id"])] = int(team["Id"])
    logging.debug("Portainer teams: " + str(portainer_teams))


def portainer_request(method, url, json={}):
    logging.debug(url + " " + method + " " + str(json))
    f = {
        "DELETE": requests.delete,
        "GET": requests.get,
        "POST": requests.post,
        "PUT": requests.put
    }[method]
    r = f(PORTAINER_API_URL + url, json=json,
        headers={
            "Authorization": "Bearer " + portainer_token
        })
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    load_env()
    portainer_init()
    docker_listen()
