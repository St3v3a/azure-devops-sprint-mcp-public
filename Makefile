# Makefile for Azure DevOps Sprint MCP Server
# Convenience commands for Docker operations

.PHONY: help build run stop logs test clean push deploy

# Variables
IMAGE_NAME ?= azure-devops-sprint-mcp
TAG ?= latest
ACR_NAME ?= acrazuredevopsmcp
ACR_LOGIN_SERVER ?= $(ACR_NAME).azurecr.io

help: ## Show this help message
	@echo "Azure DevOps Sprint MCP - Docker Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Local Development
build: ## Build Docker image locally
	docker build -t $(IMAGE_NAME):$(TAG) .

build-dev: ## Build development Docker image
	docker build -f Dockerfile.dev -t $(IMAGE_NAME):dev .

run: ## Run container with docker-compose
	docker-compose up -d

run-dev: ## Run container in development mode
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

stop: ## Stop running containers
	docker-compose down

restart: ## Restart containers
	docker-compose restart

logs: ## View container logs
	docker-compose logs -f

shell: ## Open shell in running container
	docker-compose exec mcp-server /bin/bash

python-shell: ## Open Python shell in running container
	docker-compose exec mcp-server python

# Testing
test: ## Run tests in container
	docker-compose exec mcp-server pytest

test-coverage: ## Run tests with coverage
	docker-compose exec mcp-server pytest --cov=src --cov-report=html

test-watch: ## Run tests in watch mode
	docker-compose exec mcp-server pytest-watch

# Azure Container Registry
acr-login: ## Login to Azure Container Registry
	az acr login --name $(ACR_NAME)

acr-build: ## Build image in Azure Container Registry
	az acr build --registry $(ACR_NAME) --image $(IMAGE_NAME):$(TAG) .

acr-push: build acr-login ## Build locally and push to ACR
	docker tag $(IMAGE_NAME):$(TAG) $(ACR_LOGIN_SERVER)/$(IMAGE_NAME):$(TAG)
	docker push $(ACR_LOGIN_SERVER)/$(IMAGE_NAME):$(TAG)

acr-list: ## List images in ACR
	az acr repository list --name $(ACR_NAME) -o table
	@echo ""
	az acr repository show-tags --name $(ACR_NAME) --repository $(IMAGE_NAME) -o table

# Azure Deployment
deploy-aci: ## Deploy to Azure Container Instances
	@echo "Deploying to ACI..."
	@bash scripts/deploy-aci.sh

deploy-aks: ## Deploy to Azure Kubernetes Service
	@echo "Deploying to AKS..."
	kubectl apply -f k8s-deployment.yaml

# Cleanup
clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

clean-all: ## Clean up all Docker resources including images
	docker-compose down -v --rmi all
	docker system prune -af

# Utilities
validate: ## Validate docker-compose configuration
	docker-compose config

ps: ## Show running containers
	docker-compose ps

stats: ## Show container resource usage
	docker stats

inspect: ## Inspect container
	docker-compose exec mcp-server env

# Version info
version: ## Show version information
	@echo "Docker version:"
	@docker --version
	@echo ""
	@echo "Docker Compose version:"
	@docker-compose --version
	@echo ""
	@echo "Image info:"
	@docker images $(IMAGE_NAME)
