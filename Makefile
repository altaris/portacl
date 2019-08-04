IMAGE = portacl
SUDO = sudo

all: build

build:
	$(SUDO) docker build -t $(IMAGE):$$(git rev-parse --abbrev-ref HEAD) .

create-dummy-containers:
	@$(SUDO) docker run --detach --rm --name tinky-winky	\
		--label "io.portainer.uac.public=true"  			\
		--label "io.portainer.uac.teams=1,2" 				\
		alpine sleep 600
	@$(SUDO) docker run --detach --rm --name dipsy 			\
		--label "io.portainer.uac.public=true"  			\
		--label "io.portainer.uac.users=admin" 				\
		alpine sleep 600
	@$(SUDO) docker run --detach --rm --name laa-laa 		\
		--label "io.portainer.uac.public=false"  			\
		--label "io.portainer.uac.teams=1,2" 				\
		alpine sleep 600
	@$(SUDO) docker run --detach --rm --name po 			\
		--label "io.portainer.uac.public=false"  			\
		--label "io.portainer.uac.users=admin" 				\
		alpine sleep 600

remove-dummy-containers:
	@$(SUDO) docker container rm --force tinky-winky
	@$(SUDO) docker container rm --force dipsy
	@$(SUDO) docker container rm --force laa-laa
	@$(SUDO) docker container rm --force po

.ONESHELL:
run:
	@. venv/bin/activate
	@export $$(cat secret.env | xargs)
	@$(SUDO) --preserve-env $$(which python) portacl.py
