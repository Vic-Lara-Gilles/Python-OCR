.PHONY: help start stop build rebuild logs clean dev shell status \
        install hooks test test-docker lint format typecheck check

COMPOSE ?= docker compose
DEV_COMPOSE := $(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml
PYTHON ?= python3

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

## --- Docker ---------------------------------------------------------------

start: ## Start the OCR application in the background
	$(COMPOSE) up -d

stop: ## Stop the OCR application
	$(COMPOSE) down

build: ## Build the runtime image
	$(COMPOSE) build

rebuild: ## Rebuild and restart the application
	$(COMPOSE) up --build -d

dev: ## Start in development mode with hot reload (attached)
	$(DEV_COMPOSE) up --build

logs: ## Follow application logs
	$(COMPOSE) logs -f

status: ## Show container status
	$(COMPOSE) ps

shell: ## Open a shell inside the running container
	$(COMPOSE) exec ocr-app /bin/bash

clean: ## Stop containers and remove generated output
	$(COMPOSE) down
	rm -rf outputs/*

## --- Local development ----------------------------------------------------

install: ## Install runtime and development dependencies locally
	$(PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt

hooks: ## Install the git hooks in .githooks
	git config core.hooksPath .githooks
	@echo "git hooks installed: $$(ls .githooks | tr '\n' ' ')"

test: ## Run the test suite locally
	$(PYTHON) -m pytest tests/ --cov=src/ocr --cov-report=term-missing

test-docker: ## Run the test suite inside the dev image (includes Tesseract)
	docker build --target dev -t python-ocr:dev .
	docker run --rm python-ocr:dev pytest tests/

lint: ## Check formatting and lint rules
	$(PYTHON) -m ruff check src/ tests/
	$(PYTHON) -m black --check src/ tests/

format: ## Auto-format the code base
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m ruff check --fix src/ tests/

typecheck: ## Run static type checking
	$(PYTHON) -m mypy src/ocr

check: lint typecheck test ## Run every quality gate
