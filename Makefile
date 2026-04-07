.PHONY: install test lint format clean

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
