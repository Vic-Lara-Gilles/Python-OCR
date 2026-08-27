.PHONY: help build run test vet clean docker-build docker-run docker-stop fmt lint mod

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the application
	go build -o bin/ocr-server ./cmd/server

run: ## Run the application locally
	go run ./cmd/server

test: ## Run tests
	go test -race -cover ./...

vet: ## Run go vet
	go vet ./...

clean: ## Clean build artifacts
	rm -rf bin/ outputs/*

docker-build: ## Build Docker image
	docker compose build

docker-run: ## Run with Docker Compose
	docker compose up

docker-run-d: ## Run with Docker Compose in background
	docker compose up -d

docker-stop: ## Stop Docker containers
	docker compose down

docker-logs: ## Show Docker logs
	docker compose logs -f

fmt: ## Format code
	go fmt ./...

lint: ## Run linter
	golangci-lint run

mod: ## Download dependencies
	go mod download
	go mod tidy
