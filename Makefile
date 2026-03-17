.PHONY: install test test-fast lint format serve run start validate clean

install:
	uv sync --all-extras

test:
	uv run pytest tests/ -v --tb=short

test-fast:
	uv run pytest tests/unit/ -v --tb=short -m "not slow"

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

serve:
	uv run maestro serve $(ARGS)

run:
	uv run maestro run $(ARGS)

start:
	uv run maestro start $(ARGS)

validate:
	uv run maestro validate $(ARGS)

snapshot-update:
	uv run pytest tests/unit/ -v --snapshot-update

clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
