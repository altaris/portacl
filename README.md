portacl
=======

[![Docker Build Status](https://img.shields.io/docker/build/altaris/docker-texlive.svg)](https://hub.docker.com/r/altaris/docker-texlive/)
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
- [ ] `container_exec_create`
- [x] `volume_create`
- [ ] `volume_mount`
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