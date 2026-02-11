.PHONY: help install deps dev up down clean test test-watch lint format check logs db-shell redis-shell build deploy deploy-status logs-prod

# Colors for pretty output
BLUE := \033[36m
GREEN := \033[32m
RED := \033[31m
RESET := \033[0m

##@ General

help: ## Display this help message
	@echo "$(BLUE)URL Shortener - Available Commands$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(BLUE)<target>$(RESET)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n%s\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

################################################################################
# DEV - Local Development
################################################################################

##@ [DEV] Setup

install: ## [DEV] Install dependencies
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	poetry install

##@ [DEV] Local Development

deps: ## [DEV] Start infra (shared-postgres + redis)
	cd ../shared-postgres && docker compose up -d
	docker compose up redis -d

dev: deps ## [DEV] Start native dev server (uvicorn --reload)
	poetry run uvicorn app.main:app --reload --port 8000

##@ [DEV] Docker

up: ## [DEV] Start all services in Docker
	docker compose up -d --build

down: ## [DEV] Stop services
	docker compose down

logs: ## [DEV] Show container logs
	docker compose logs -f

##@ [DEV] Testing

test: ## [DEV] Run all tests
	@echo "$(BLUE)Running tests...$(RESET)"
	poetry run pytest -v

test-watch: ## [DEV] Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(RESET)"
	poetry run pytest-watch

test-cov: ## [DEV] Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	poetry run pytest --cov=app --cov-report=html --cov-report=term

##@ [DEV] Code Quality

lint: ## [DEV] Lint code with ruff
	@echo "$(BLUE)Linting code...$(RESET)"
	poetry run ruff check app/

format: ## [DEV] Format code with black
	@echo "$(BLUE)Formatting code...$(RESET)"
	poetry run black app/

check: lint ## [DEV] Run all checks (lint)
	@echo "$(GREEN)All checks passed!$(RESET)"

##@ [DEV] Database

db-shell: ## [DEV] Open PostgreSQL shell (shared-postgres)
	docker exec -it shared-postgres psql -U shortener -d shortener

redis-shell: ## [DEV] Open Redis CLI
	docker exec -it url-shortener-redis redis-cli

##@ [DEV] Utilities

build: ## [DEV] Build production Docker image locally
	@echo "$(BLUE)Building production image...$(RESET)"
	docker compose build

clean: ## [DEV] Clean up (pytest cache, coverage reports)
	@echo "$(BLUE)Cleaning up...$(RESET)"
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(RESET)"

################################################################################
# PROD - Production Deployment
################################################################################

# Configuration
DEPLOY_HOST ?= web-01
DEPLOY_PATH ?= /home/victor/projects/url-shortener
DEPLOY_BRANCH ?= main

##@ [PROD] Deployment

deploy: ## [PROD] Deploy to production server
	@echo "$(BLUE)Deploying to production...$(RESET)"
	@echo "$(BLUE)Step 1/4: Running local tests...$(RESET)"
	@poetry run pytest -q || { echo "$(RED)Tests failed! Aborting deploy.$(RESET)"; exit 1; }
	@echo "$(BLUE)Step 2/4: Deploying to $(DEPLOY_HOST)...$(RESET)"
	@ssh $(DEPLOY_HOST) '\
		cd $(DEPLOY_PATH) && \
		echo "Pulling latest code..." && \
		git pull origin $(DEPLOY_BRANCH) && \
		echo "Building Docker image..." && \
		docker compose build && \
		echo "Restarting containers..." && \
		docker compose down && \
		docker compose up -d && \
		echo "Deployment complete!" \
	'
	@echo "$(BLUE)Step 3/4: Verifying deployment...$(RESET)"
	@sleep 5
	@curl -sf https://s.victorpatrin.dev/health && echo "$(GREEN)✅ Deployment successful!$(RESET)" || echo "$(RED)⚠️  Health check failed$(RESET)"

deploy-status: ## [PROD] Check deployment status
	@echo "$(BLUE)Checking deployment status...$(RESET)"
	@ssh $(DEPLOY_HOST) '\
		cd $(DEPLOY_PATH) && \
		echo "=== Git Status ===" && \
		git log -1 --oneline && \
		echo "" && \
		echo "=== Docker Containers ===" && \
		docker compose ps && \
		echo "" && \
		echo "=== Recent Logs ===" && \
		docker compose logs --tail=20 \
	'

##@ [PROD] Monitoring

logs-prod: ## [PROD] Show production logs (live tail)
	@echo "$(BLUE)Tailing production logs from $(DEPLOY_HOST)...$(RESET)"
	@ssh $(DEPLOY_HOST) '\
		cd $(DEPLOY_PATH) && \
		docker compose logs -f \
	'
