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
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo ""
	@echo "$(GREEN)Data:$(NC)"
	@echo "  make seed         - Seed database with sample data"
	@echo "  make shell        - Open Django shell"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-up    - Start all services"
	@echo "  make docker-down  - Stop all services"
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

# Development
dev:
	@echo "$(CYAN)Starting DSMS Django API...$(NC)"
	@echo "Django API: http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	python dev.py

# Testing
test:
	@echo "$(CYAN)Running tests...$(NC)"
	cd src/dsms && venv/Scripts/python manage.py test

lint:
	@echo "$(CYAN)Running linters...$(NC)"
	cd src/dsms && venv/Scripts/flake8 --max-line-length=100

format:
	@echo "$(CYAN)Formatting code...$(NC)"
	cd src/dsms && venv/Scripts/black .

# Data
seed:
	@echo "$(CYAN)Seeding database...$(NC)"
	cd src/dsms && venv/Scripts/python scripts/seed_data.py

shell:
	cd src/dsms && venv/Scripts/python manage.py shell

# Docker
docker-up:
	docker-compose -f docker-compose.dev.yml up -d

docker-down:
	docker-compose -f docker-compose.dev.yml down

# Cleanup
clean:
	@echo "$(CYAN)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)[OK] Cleaned!$(NC)"
