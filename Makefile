.PHONY: help install dev up down clean test test-watch lint format check logs db-shell redis-shell build deploy

# Colors for pretty output
BLUE := \033[36m
RESET := \033[0m

##@ General

help: ## Display this help message
	@echo "$(BLUE)URL Shortener - Development Commands$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(BLUE)<target>$(RESET)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n%s\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development Setup

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	poetry install

setup: install ## Initial setup (install deps + create .env)
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@if [ ! -f .env ]; then \
		cp .env.local .env; \
		echo "$(BLUE)Created .env from .env.local$(RESET)"; \
	fi

##@ Development

dev: setup up ## Full dev environment (setup + start databases)
	@echo ""
	@echo "$(BLUE)✅ Development environment ready!$(RESET)"
	@echo ""
	@echo "Run the app with:"
	@echo "  make run"

up: ## Start databases (PostgreSQL + Redis)
	@echo "$(BLUE)Starting databases...$(RESET)"
	docker compose -f docker-compose.dev.yml up -d
	@echo "$(BLUE)Waiting for databases...$(RESET)"
	@sleep 3

down: ## Stop databases
	@echo "$(BLUE)Stopping databases...$(RESET)"
	docker compose -f docker-compose.dev.yml down

run: ## Run the application with hot reload
	@echo "$(BLUE)Starting FastAPI with hot reload...$(RESET)"
	@echo "Access at: http://localhost:8000"
	@echo "API docs:  http://localhost:8000/docs"
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(RESET)"
	poetry run pytest -v

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(RESET)"
	poetry run pytest-watch

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	poetry run pytest --cov=app --cov-report=html --cov-report=term

##@ Code Quality

lint: ## Lint code with ruff
	@echo "$(BLUE)Linting code...$(RESET)"
	poetry run ruff check app/

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(RESET)"
	poetry run black app/

check: lint ## Run all checks (lint)
	@echo "$(BLUE)All checks passed!$(RESET)"

##@ Database

db-shell: ## Open PostgreSQL shell
	docker exec -it url-shortener-db-dev psql -U postgres -d shortener

redis-shell: ## Open Redis CLI
	docker exec -it url-shortener-redis-dev redis-cli

##@ Docker

build: ## Build production Docker image
	@echo "$(BLUE)Building production image...$(RESET)"
	docker compose build

##@ Utilities

logs: ## Show database logs
	docker compose -f docker-compose.dev.yml logs -f

clean: down ## Clean up (stop containers + remove volumes)
	@echo "$(BLUE)Cleaning up...$(RESET)"
	docker compose -f docker-compose.dev.yml down -v
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(BLUE)Cleanup complete!$(RESET)"
