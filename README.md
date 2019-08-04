portacl
=======

Updates [portainer](https://www.portainer.io/) ACLs from container labels.

# Usage

```sh
./portacl.py
```

The script does not take command line arguments, but reads the following
environment variables.

* `DOCKER_CERT_PATH`: See the [Docker SDK
  documentation](https://docker-py.readthedocs.io/en/stable/client.html#creating-a-client).
* `DOCKER_HOST`: See the [Docker SDK
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
make run
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