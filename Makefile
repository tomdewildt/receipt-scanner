.PHONY: init run/dev run/prod build/dev build/prod deploy/dev deploy/prod test lint
.DEFAULT_GOAL := help

NAMESPACE := tomdewildt
NAME := receipt-scanner

IMAGE := $(subst -,_,$(NAMESPACE))_$(subst -,_,$(NAME))

export PYTHONPATH=src:test

help: ## Show this help
	@echo "${NAMESPACE}/${NAME}"
	@echo
	@fgrep -h "##" $(MAKEFILE_LIST) | \
	fgrep -v fgrep | sed -e 's/## */##/' | column -t -s##

##

init: ## Initialize the environment
	for f in requirements/*.txt; do \
		pip install -r "$$f"; \
	done

##

notebook: ## Run the notebook server
	jupyter lab

##

run/dev: ## Run development app
	docker run --rm -it -p 8080:8080 -v ${PWD}/src:/opt/service/src --name ${IMAGE}_dev ${IMAGE}_dev:latest

run/prod: ## Run production app
	docker run --rm -it -p 8080:8080 --name ${IMAGE}_prod ${IMAGE}_prod:latest

##

build/dev: ## Build development app
	docker build --tag ${IMAGE}_dev:latest --file Dockerfile.dev .

build/prod: ## Build production app
	docker build --tag ${IMAGE}_prod:latest --file Dockerfile.prod .

##

deploy/dev: ## Deploy development app
	@echo "Error: Not Implemented"

deploy/prod: ## Deploy production app
	@echo "Error: Not Implemented"

##

test: ## Run tests
	pytest test

##

lint: ## Run lint
	pylint src test
