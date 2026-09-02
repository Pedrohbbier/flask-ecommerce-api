# ---------------------------------------------------------------------------
# E-commerce API - developer commands
# ---------------------------------------------------------------------------
# Load the project settings so the targets print the same ports Compose uses.
-include .env

APP_PORT ?= 5001
PMA_PORT ?= 8080

COMPOSE := docker compose
API     := $(COMPOSE) exec api

.DEFAULT_GOAL := help
.PHONY: help setup build up down restart logs ps shell db-shell \
        migrate upgrade downgrade history seed wipe reset docs pma clean

help: ## Show the available commands
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Create .env from the example file (first run)
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")

build: setup ## Build the API image
	$(COMPOSE) build

up: setup ## Start MySQL and the API in the background (migrations run automatically)
	$(COMPOSE) up -d --build
	@echo "API:        http://localhost:$(APP_PORT)"
	@echo "Swagger:    http://localhost:$(APP_PORT)/docs"
	@echo "phpMyAdmin: http://localhost:$(PMA_PORT)"

down: ## Stop the containers
	$(COMPOSE) down

restart: ## Restart the API container
	$(COMPOSE) restart api

logs: ## Follow the API logs
	$(COMPOSE) logs -f api

ps: ## Show container status
	$(COMPOSE) ps

shell: ## Open a shell inside the API container
	$(API) bash

db-shell: ## Open a MySQL client on the database
	$(COMPOSE) exec db sh -c 'mysql -u$$MYSQL_USER -p$$MYSQL_PASSWORD $$MYSQL_DATABASE'

migrate: ## Autogenerate a migration: make migrate m="message"
	$(API) flask db migrate -m "$(m)"

upgrade: ## Apply pending migrations
	$(API) flask db upgrade

downgrade: ## Roll back the last migration
	$(API) flask db downgrade

history: ## Show the migration history
	$(API) flask db history

seed: ## Populate the database with demo data
	$(API) flask seed

wipe: ## Delete every row, keeping the schema
	$(API) flask wipe

reset: ## Drop volumes, rebuild, migrate and seed from scratch
	$(COMPOSE) down -v
	$(COMPOSE) up -d --build
	@echo "Waiting for the API to become healthy..."
	@until curl -sf http://localhost:$(APP_PORT)/api/v1/health > /dev/null; do sleep 2; done
	$(API) flask seed
	@echo "Environment ready:"
	@echo "  Swagger:    http://localhost:$(APP_PORT)/docs"
	@echo "  phpMyAdmin: http://localhost:$(PMA_PORT)"

pma: ## Open phpMyAdmin in the browser
	@open http://localhost:$(PMA_PORT) 2>/dev/null \
		|| xdg-open http://localhost:$(PMA_PORT) 2>/dev/null \
		|| echo "Open http://localhost:$(PMA_PORT)"

docs: ## Open the Swagger UI in the browser
	@open http://localhost:$(APP_PORT)/docs 2>/dev/null \
		|| xdg-open http://localhost:$(APP_PORT)/docs 2>/dev/null \
		|| echo "Open http://localhost:$(APP_PORT)/docs"

clean: ## Remove containers, volumes and local caches
	$(COMPOSE) down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
