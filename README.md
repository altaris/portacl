portacl
=======

**With the resolution of portainer's issue
[#3337](https://github.com/portainer/portainer/pull/3337), this project is
deprecated.**

[![Docker Build Status](https://img.shields.io/docker/cloud/build/altaris/portacl)](https://hub.docker.com/r/altaris/portacl/)
[![Maintainability](https://api.codeclimate.com/v1/badges/34e440aee948a0bc7b21/maintainability)](https://codeclimate.com/github/altaris/portacl/maintainability)
![Python 3](https://badgen.net/badge/Python/3/blue)
[![MIT License](https://badgen.net/badge/license/MIT/blue)](https://choosealicense.com/licenses/mit/)

Updates [portainer](https://www.portainer.io/) ACLs from container labels.

# Usage

```sh
docker run --detach                                       \
    --env "PORTAINER_API_PASSWORD=password"               \
    --env "PORTAINER_API_URL=http://localhost:9000/api"   \
    --env "PORTAINER_API_USERNAME=admin"                  \
    --network host                                        \
    --volume /var/run/docker.sock:/var/run/docker.sock:ro \
    altaris/portacl
```

## Environment variables

* `DOCKER_CERT_PATH`: See the [Docker SDK
  documentation](https://docker-py.readthedocs.io/en/stable/client.html#creating-a-client).
* `DOCKER_HOST` (default: `unix:///var/run/docker.sock`): See the [Docker SDK
  documentation](https://docker-py.readthedocs.io/en/stable/client.html#creating-a-client).
* `DOCKER_TLS_VERIFY`: See the [Docker SDK
  documentation](https://docker-py.readthedocs.io/en/stable/client.html#creating-a-client).
* `LOGGING_LEVEL` (default: `WARNING`): Python logging level, see
  [here](https://docs.python.org/2/library/logging.html#logging-levels).
* `PORTAINER_API_PASSWORD`.
* `PORTAINER_API_USERNAME`.
* `PORTAINER_API_URL`.

# Labels

Based on [this portainer issue on
github](https://github.com/portainer/portainer/issues/1257#issuecomment-414221956):
* `io.portainer.uac.public` (default: `false`).
* `io.portainer.uac.teams`: Comma separated list of authorized teams,
  identified by name (which is assumes not to start with a digit) or an id.
* `io.portainer.uac.users`: Comma separated list of authorized users,
  identified by name (which is assumes not to start with a digit) or an id.

# Supported events

`portacl` will create, update, or delete ACLs upon receiving docker events.
Here is a list of supported and soon (:tm:) to be supported events.
- [x] `container_create`
- [x] `volume_create`
- [ ] `volume_mount`: WIP. For the time being, please set adequate ACLs to
  volume shared among multiple containers.
- [ ] `volume_unmount`
- [ ] `service_create`
- [ ] `service_update`
- [ ] `secret_create`

# Known issues :sweat_smile:

* portacl does not manage ACLs of ressources created before it has started.
* API requests setting a volume as piublic always fail. This seems to be a
  portainer issue.
* This list should probably be repo issues instead of in the readme.

# Testing

1. Start the portainer test instance:
```sh
make test-portainer-up
```
2. Start portacl:
```sh
# a) direct mode (run this on a dedicated terminal)
make run
#    you can also set environment variables, e.g.
LOGGING_LEVEL=WARNING make run
# b) dockerized mode
make run-docker
```
3. Start the test stack (press Ctrl+C to exit):
```sh
make test-stack-up
```
4. Cleanup after yourself:
```sh
make test-stack-down
make test-portainer-down
```

## The test portainer instance

The users and teams are as follows:

| User     | Id | Password   |
|----------|----|------------|
| `admin`  | 1  | `password` |
| `bob`    | 2  | `password` |
| `carol`  | 3  | `password` |
| `daniel` | 4  | `password` |

| Team          | Id | Members            |
|---------------|----|--------------------|
| `development` | 1  | `bob` & `carol`    |
| `qa`          | 2  | `carol`            |
| `production`  | 3  | `carol` & `daniel` |

To make API calls to the test portainer instance:
```sh
. ./test/test-portainer-connect.sh
portainer_api_call "METHOD" "PATH" "JSON_ARGUMENTS_IF_NEEDED"
portainer_api_call "GET" "/users" | jq
```

# References

* [Portainer API](https://app.swaggerhub.com/apis/deviantony/Portainer/1.22.0/)
* [Docker API](https://docs.docker.com/engine/api/v1.30/)