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
# Requires a valid secret.env file, see secret.env.example
make run
# On a separate terminal
make create-dummy-containers
make remove-dummy-containers
```
