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
* `DOCKER_HOST` (default: `unix://var/run/docker.sock`): See the [Docker SDK
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
  identified by name (which is assume to not start by a digit) or an id.
* `io.portainer.uac.users`: Comma separated list of authorized users,
  identified by name (which is assume to not start by a digit) or an id.

# Testing

```sh
# Start test portainer instance
make test-portainer-up
# Start portacl (run this on a dedicated terminal)
make run  # or make run-docker to run in dockerized environment
# Start test stack (press Ctrl+C to exit)
make test-stack-up
# Cleanup
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