# Workflow Tracker — operational shortcuts.

COMPOSE ?= docker compose

.PHONY: help build up down logs restart clean test backend-shell migrate \
        createsuperuser backend-install frontend-install dev-backend dev-frontend

help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Docker 
build: ## Build all Docker images
	$(COMPOSE) build

up: ## Start the stack in the background
	$(COMPOSE) up -d

down: ## Stop and remove containers (keeps the SQLite volume)
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

restart: down up ## Restart the stack

clean: ## Stop the stack and DROP all volumes, images and networks
	$(COMPOSE) down -v --rmi local --remove-orphans

# Container 
backend-shell: ## Open a shell inside the backend container
	$(COMPOSE) exec backend sh

migrate: ## Apply Django migrations
	$(COMPOSE) exec backend python3 manage.py migrate

createsuperuser: ## Create a Django admin superuser (interactive)
	$(COMPOSE) exec -it backend python3 manage.py createsuperuser

test: ## Run backend tests inside the container
	$(COMPOSE) exec backend python3 manage.py test

# Local
backend-install: ## Install Python deps locally (no Docker)
	cd backend && pip install -r requirements.txt

frontend-install: ## Install frontend deps locally (no Docker)
	cd frontend && npm install

dev-backend: ## Run Django dev server locally
	cd backend && python3 manage.py migrate && python3 manage.py runserver

dev-frontend: ## Run Next.js dev server locally
	cd frontend && npm run dev
