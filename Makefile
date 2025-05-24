.PHONY: clean seed run test coverage install logs

# Variables
PYTHON = python3
COVERAGE = coverage
REDIS_CLI = redis-cli
MONGO_CLIENT = mongosh

# Install dependencies
install:
	pip install -r requirements.txt
	pip install coverage pytest pytest-django pytest-cov

# Clean databases
clean:
	@echo "Cleaning databases..."
	$(REDIS_CLI) FLUSHALL
	$(PYTHON) scripts/seed.py --clean
	@echo "Databases cleaned"

# Seed database with test data
seed:
	@echo "Seeding database..."
	$(PYTHON) scripts/seed.py
	@echo "Database seeded"

# Run development server
run:
	@echo "Starting development server..."
	$(PYTHON) manage.py runserver

# Run tests
test:
	pytest

# Run tests with coverage
coverage:
	$(COVERAGE) run -m pytest
	$(COVERAGE) report
	$(COVERAGE) html
	@echo "Coverage report generated in htmlcov/index.html"

# Create necessary directories
setup:
	mkdir -p logs
	mkdir -p static
	touch logs/debug.log

# View logs
logs:
	tail -f logs/debug.log

# Help
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make clean      - Clean all databases"
	@echo "  make seed       - Seed database with test data"
	@echo "  make run        - Run development server"
	@echo "  make test       - Run tests"
	@echo "  make coverage   - Run tests with coverage report"
	@echo "  make setup      - Create necessary directories"
	@echo "  make logs       - View application logs" 