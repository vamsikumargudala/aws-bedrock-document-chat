.PHONY: help install test test-unit test-integration coverage docker-build docker-up docker-down clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies
	uv pip install --system -r pyproject.toml
	uv pip install --system pytest pytest-asyncio pytest-cov httpx pytest-mock

test: ## Run all tests
	@$(MAKE) test-unit
	@$(MAKE) test-integration

test-unit: ## Run unit tests
	cd server && python -m pytest ../tests/unit/ -v --tb=short

test-integration: ## Run integration tests
	python -m pytest tests/integration/ -v --tb=short

coverage: ## Run tests with coverage report
	cd server && python -m pytest ../tests/ -v --cov=. --cov-report=html --cov-report=term-missing

docker-build: ## Build Docker containers
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

dev-server: ## Start development server
	cd server && uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-client: ## Start development client
	cd client && python3 -m http.server 3000

clean: ## Clean up generated files
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -rf server/htmlcov/ server/.coverage .pytest_cache/