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

def loadEnv():
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
    r = requests.post(PORTAINER_API_URL + "/auth",
        json={
            "Password": PORTAINER_API_PASSWORD,
            "Username": PORTAINER_API_USERNAME
    })
    r.raise_for_status()
    global portainer_token
    portainer_token = r.json()["jwt"]
    for user in portainer_request("GET", "/users"):
        portainer_users[user["Username"]] = user["Id"]
    logging.debug("Portainer users: " + str(portainer_users))
    for team in portainer_request("GET", "/teams"):
        portainer_teams[team["Name"]] = team["Id"]
    logging.debug("Portainer teams: " + str(portainer_teams))


def portainer_request(method, url, json={}):
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
    loadEnv()

    logging.info("Authenticating to portainer api {}".format(PORTAINER_API_URL))
    portainer_init()
