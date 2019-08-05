DOCKER_COMPOSE 	= docker-compose -f test/test-stack.yml -p portacl-test-stack
IMAGE 			= portacl
SUDO 			= sudo

all: build

build:
	$(SUDO) docker build -t $(IMAGE):$$(git rev-parse --abbrev-ref HEAD) .

clean: test-stack-down test-portainer-down

.ONESHELL:
run:
	. venv/bin/activate
	export LOGGING_LEVEL=DEBUG
	export PORTAINER_API_PASSWORD=password
	export PORTAINER_API_URL=http://localhost:9000/api
	export PORTAINER_API_USERNAME=admin
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

test-stack-down:
	$(SUDO) $(DOCKER_COMPOSE) down -v

test-stack-up:
	$(SUDO) $(DOCKER_COMPOSE) up
