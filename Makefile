COMPOSE = sudo docker compose -f test-cluster/docker-compose.yml
TOKEN = $(shell $(COMPOSE) exec -T slurmctld scontrol token username=alice lifespan=3600 2>/dev/null | grep SLURM_JWT | cut -d= -f2)

.PHONY: up down build rebuild submit shell squeue sinfo rest-token rest-ping rest-jobs logs clean build-linux build-host stui-local stui-rest

## Build stui
build-linux: ## Cross-compile stui for linux/amd64
	GOOS=linux GOARCH=amd64 go build -o stui

build-host: ## Build stui for host
	go build -o stui

## Run stui
stui-local: build-linux ## Run stui inside the cluster (local backend)
	$(COMPOSE) exec slurmctld /app/stui

stui-rest: build-host ## Run stui against REST API from host
	./stui

## Cluster lifecycle
up: ## Start the test cluster
	$(COMPOSE) up -d

down: ## Stop the test cluster
	$(COMPOSE) down

build: ## Build images
	$(COMPOSE) build

rebuild: ## Rebuild images from scratch and start
	$(COMPOSE) up -d --build

## Jobs
submit: ## Submit fake jobs from multiple users
	$(COMPOSE) exec slurmctld bash /opt/submit_fake_jobs.sh

## Inspection
shell: ## Get an interactive shell on slurmctld
	$(COMPOSE) exec slurmctld bash

squeue: ## Show job queue
	$(COMPOSE) exec slurmctld squeue

sinfo: ## Show node/partition status
	$(COMPOSE) exec slurmctld sinfo

## REST API
rest-token: ## Generate a JWT token for user alice (valid 1 hour)
	$(COMPOSE) exec slurmctld scontrol token username=alice lifespan=3600

rest-ping: ## Test REST API ping
	@curl -s -H "X-SLURM-USER-NAME: alice" -H "X-SLURM-USER-TOKEN: $(TOKEN)" http://localhost:6820/slurm/v0.0.37/ping

rest-jobs: ## Get jobs via REST API
	@curl -s -H "X-SLURM-USER-NAME: alice" -H "X-SLURM-USER-TOKEN: $(TOKEN)" http://localhost:6820/slurm/v0.0.37/jobs

logs: ## Tail logs from all containers
	$(COMPOSE) logs -f

logs-ctrl: ## Tail slurmctld logs only
	$(COMPOSE) logs -f slurmctld

## Cleanup
clean: ## Stop cluster and remove volumes
	$(COMPOSE) down -v --rmi local

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
