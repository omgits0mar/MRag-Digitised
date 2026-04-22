.PHONY: install test lint format clean \
    docker-build docker-up docker-down docker-logs docker-restart docker-ps \
    docker-backend-shell docker-test

install:
	pip install -e ".[dev]"

test:
	python -m pytest --cov=mrag --cov-report=term-missing tests/

lint:
	ruff check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov dist build *.egg-info .pytest_cache .ruff_cache

# --- Docker ------------------------------------------------------------------
docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-restart:
	docker compose restart

docker-logs:
	docker compose logs -f --tail=200

docker-ps:
	docker compose ps

docker-backend-shell:
	docker compose exec backend /bin/bash

docker-test:
	docker compose run --rm backend python -m pytest tests/
