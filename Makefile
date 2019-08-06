DOCKER_COMPOSE 	 = docker-compose -f test/test-stack.yml -p portacl-test-stack
IMAGE 			 = portacl
SUDO 			?= sudo

LOGGING_LEVEL			?= DEBUG
PORTAINER_API_PASSWORD	?= password
PORTAINER_API_URL		?= http://localhost:9000/api
PORTAINER_API_USERNAME	?= admin

all: build

build:
	$(SUDO) docker build -t $(IMAGE):$$(git rev-parse --abbrev-ref HEAD) .

clean: test-stack-down test-portainer-down

.ONESHELL:
run:
	. venv/bin/activate
	export LOGGING_LEVEL="$(LOGGING_LEVEL)"
	export PORTAINER_API_PASSWORD="$(PORTAINER_API_PASSWORD)"
	export PORTAINER_API_URL="$(PORTAINER_API_URL)"
	export PORTAINER_API_USERNAME="$(PORTAINER_API_USERNAME)"
	$(SUDO) --preserve-env $$(which python) portacl.py

run-docker: build
	$(SUDO) docker run --rm										\
		--env "LOGGING_LEVEL=DEBUG"								\
		--env "PORTAINER_API_PASSWORD=password"					\
		--env "PORTAINER_API_URL=http://localhost:9000/api"		\
		--env "PORTAINER_API_USERNAME=admin"					\
		--name portacl-test										\
		--network host											\
		--volume /var/run/docker.sock:/var/run/docker.sock:ro	\
		$(IMAGE):$$(git rev-parse --abbrev-ref HEAD)

test-portainer-down:
	$(SUDO) docker container rm --force portacl-test-portainer

test-portainer-up:
	@./test/test-portainer-up.sh

test-stack-create:
	$(SUDO) $(DOCKER_COMPOSE) create

test-stack-down:
	$(SUDO) $(DOCKER_COMPOSE) down -v

test-stack-up:
	$(SUDO) $(DOCKER_COMPOSE) up
