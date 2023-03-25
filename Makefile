#!/usr/bin/env make

SHELL="/bin/bash"
NAME="irrigation"
TAG="procamora:$(NAME)"

.PHONY: help help shell run


all: build run


build: ## Build a dockerimage
	#@docker build --no-cache --tag "$(TAG)" -f ./Dockerfile .
	@docker build --tag "$(TAG)" -f ./Dockerfile .

run:
	@docker run --privileged -ti --rm  \
	  -v ${PWD}/settings.cfg:/data/settings.cfg \
	  -v ${PWD}/token.json:/data/token.json \
	  -v ${PWD}/credentials.json:/data/credentials.json \
      -p 4772:22 --name "$(NAME)" --hostname="$(NAME)" "$(TAG)"

help: ## Print this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

shell: ## shell inside docker container
	@docker exec -ti  "$(NAME)" /bin/bash

ssh: ## shell inside docker container with SSH
	@ssh -i ~/.ssh/bbva -p 2222 root@127.0.0.1

