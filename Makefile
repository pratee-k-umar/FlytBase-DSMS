.PHONY: help setup dev test lint format seed docker-up docker-down clean

# Colors
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help:
	@echo "$(CYAN)DSMS Development Commands$(NC)"
	@echo "========================="
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make setup        - Install backend dependencies"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev          - Run Django development server"
	@echo "  make dev-docker   - Start local MongoDB & Redis containers"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test         - Run all tests"
	@echo "  make test-api     - Run API endpoint tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo ""
	@echo "$(GREEN)Data:$(NC)"
	@echo "  make seed         - Seed database with sample data"
	@echo "  make shell        - Open Django shell"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-dev   - Start dev services (MongoDB, Redis)"
	@echo "  make docker-prod  - Build and start production stack"
	@echo "  make docker-down  - Stop all containers"
	@echo "  make docker-logs  - View container logs"
	@echo ""
	@echo "$(GREEN)Build:$(NC)"
	@echo "  make build        - Build frontend for production"
	@echo "  make build-docker - Build Docker images"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean        - Remove cache files"

# Setup
setup:
	@echo "$(CYAN)Setting up backend...$(NC)"
	cd src/dsms && python -m venv venv
	cd src/dsms && venv/Scripts/pip install -r requirements.txt
	cp .env.example .env 2>/dev/null || true
	@echo "$(GREEN)[OK] Setup complete!$(NC)"
	@echo "Configure your .env file with MongoDB and Redis URLs"

# Build (for production deployment)
build:
	@echo "$(CYAN)Installing dependencies...$(NC)"
	pip install -r src/dsms/requirements.txt
	npm install
	@echo "$(CYAN)Building frontend...$(NC)"
	npm run build
	@echo "$(GREEN)[OK] Build complete!$(NC)"

# Development
dev:
	@echo "$(CYAN)Starting DSMS Django API...$(NC)"
	@echo "Django API: http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	python dev.py

dev-docker:
	@echo "$(CYAN)Starting dev services (MongoDB, Redis)...$(NC)"
	docker compose -f docker-compose.dev.yml up -d mongodb redis
	@echo "$(GREEN)[OK] MongoDB: localhost:27017$(NC)"
	@echo "$(GREEN)[OK] Redis: localhost:6379$(NC)"

# Testing
test:
	@echo "$(CYAN)Running tests...$(NC)"
	cd src/dsms && venv/Scripts/python manage.py test

test-api:
	@echo "$(CYAN)Running API tests...$(NC)"
	python scripts/test_api.py

lint:
	@echo "$(CYAN)Running linters...$(NC)"
	cd src/dsms && venv/Scripts/flake8 --max-line-length=100

format:
	@echo "$(CYAN)Formatting code...$(NC)"
	cd src/dsms && venv/Scripts/black .

# Data
seed:
	@echo "$(CYAN)Seeding database...$(NC)"
	python scripts/seed_data.py

shell:
	cd src/dsms && venv/Scripts/python manage.py shell

# Docker
docker-dev:
	@echo "$(CYAN)Starting dev services...$(NC)"
	docker compose -f docker-compose.dev.yml up -d mongodb redis
	@echo "$(GREEN)[OK] Services started$(NC)"

docker-prod:
	@echo "$(CYAN)Building and starting production stack...$(NC)"
	docker compose up --build -d
	@echo "$(GREEN)[OK] Production stack running at http://localhost:8000$(NC)"

docker-down:
	docker compose -f docker-compose.dev.yml down 2>/dev/null || true
	docker compose down 2>/dev/null || true
	@echo "$(GREEN)[OK] All containers stopped$(NC)"

docker-logs:
	docker compose logs -f

build-docker:
	@echo "$(CYAN)Building Docker images...$(NC)"
	docker compose build
	@echo "$(GREEN)[OK] Images built$(NC)"

# Cleanup
clean:
	@echo "$(CYAN)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)[OK] Cleaned!$(NC)"

