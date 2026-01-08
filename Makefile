.PHONY: help start stop build rebuild logs clean dev test lint format

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Start the OCR application with Docker
	docker-compose up -d

stop: ## Stop the OCR application
	docker-compose down

build: ## Build the Docker image
	docker-compose build

rebuild: ## Rebuild and start the application
	docker-compose up --build -d

logs: ## Show application logs
	docker-compose logs -f

clean: ## Stop containers and clean outputs
	docker-compose down
	rm -rf outputs/* uploads/*

dev: ## Start in development mode (attached)
	docker-compose up --build

test: ## Run tests
	docker-compose exec ocr-app pytest tests/ -v

lint: ## Run linter
	docker-compose exec ocr-app ruff check src/

format: ## Format code
	docker-compose exec ocr-app ruff format src/

shell: ## Open shell in container
	docker-compose exec ocr-app /bin/bash

status: ## Show container status
	docker-compose ps
