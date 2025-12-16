.PHONY: help install dev-install test lint format clean run-app create-db run-example

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev-install  - Install development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code with black"
	@echo "  make clean        - Clean up generated files"
	@echo "  make run-app      - Run Streamlit app"
	@echo "  make create-db    - Create sample database"
	@echo "  make run-example  - Run basic usage example"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 mypy

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	flake8 src/ tests/ --max-line-length=100
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/ examples/ --line-length=100

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

run-app:
	streamlit run src/app.py

create-db:
	python examples/create_sample_db.py

run-example:
	python examples/basic_usage.py

# Docker commands (optional)
docker-build:
	docker build -t agentic-analytics .

docker-run:
	docker run -p 8501:8501 --env-file .env agentic-analytics
