DOCKER_COMPOSE 	= docker-compose -f test/test-stack.yml -p portacl-test
IMAGE 			= portacl
SUDO 			= sudo

all: build

build:
	$(SUDO) docker build -t $(IMAGE):$$(git rev-parse --abbrev-ref HEAD) .

.ONESHELL:
run:
	. venv/bin/activate
	export $$(cat test/test.env | xargs)
	$(SUDO) --preserve-env $$(which python) portacl.py

test-portainer-down:
	$(SUDO) docker container rm --force portacl-test

test-portainer-up:
	$(SUDO) docker run --detach								\
		--name portacl-test									\
		--publish 9000:9000									\
		--volume /var/run/docker.sock:/var/run/docker.sock	\
		--volume $$(pwd)/test/portainer-data:/data			\
		portainer/portainer

test-stack-down:
	$(SUDO) $(DOCKER_COMPOSE) down -v

test-stack-up:
	$(SUDO) $(DOCKER_COMPOSE) up
