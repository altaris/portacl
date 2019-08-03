IMAGE = portacl
SUDO = sudo

all: build

build:
	$(SUDO) docker build -t $(IMAGE):$$(git rev-parse --abbrev-ref HEAD) .

.ONESHELL:
run:
	@. venv/bin/activate
	@export $$(cat .env | xargs)
	@sudo --preserve-env $$(which python) portacl.py
