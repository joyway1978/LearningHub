.PHONY: help up down logs test migrate build clean restart status

# Default target
help:
	@echo "AI Learning Platform - Makefile Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup          - Initial setup (copy .env.example to .env)"
	@echo "  make build          - Build all Docker images"
	@echo ""
	@echo "Service Commands:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make status         - Show service status"
	@echo ""
	@echo "Log Commands:"
	@echo "  make logs           - View all service logs"
	@echo "  make logs-backend   - View backend logs only"
	@echo "  make logs-frontend  - View frontend logs only"
	@echo "  make logs-mysql     - View MySQL logs only"
	@echo "  make logs-minio     - View MinIO logs only"
	@echo ""
	@echo "Test Commands:"
	@echo "  make test           - Run all tests"
	@echo "  make test-backend   - Run backend tests only"
	@echo "  make test-frontend  - Run frontend tests only"
	@echo ""
	@echo "Database Commands:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make db-shell       - Open MySQL shell"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean          - Clean up containers and volumes"
	@echo "  make clean-all      - Clean everything including images"
	@echo "  make shell-backend  - Open backend container shell"
	@echo "  make shell-frontend - Open frontend container shell"

# Setup
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
		echo "Please edit .env with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

# Build
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "Services started:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  MinIO Console: http://localhost:9001"

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# Show status
status:
	docker-compose ps

# View all logs
logs:
	docker-compose logs -f

# View specific service logs
logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-mysql:
	docker-compose logs -f mysql

logs-minio:
	docker-compose logs -f minio

# Run all tests
test: test-backend test-frontend

# Run backend tests
test-backend:
	@echo "Running backend tests..."
	cd backend && pytest --cov=app tests/ -v

# Run frontend tests
test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

# Database migrations
migrate:
	@echo "Running database migrations..."
	cd backend && alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

db-shell:
	docker-compose exec mysql mysql -u root -p ai_learning

# Shell access
shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

# Cleanup
clean:
	docker-compose down -v
	docker system prune -f

clean-all: clean
	docker-compose down --rmi all -v
	docker system prune -af

# Development helpers
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Health check
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "Backend not responding"
	@curl -s http://localhost:3000 | head -1 || echo "Frontend not responding"
