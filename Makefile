.DEFAULT_GOAL := help

.PHONY: install test test-fast lint format serve run start validate clean help frontend frontend-dev up

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

up: install frontend
	uv run maestro start $(ARGS)

frontend:
	cd frontend && npm install && npm run build

frontend-dev:
	cd frontend && npm run dev

clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

help: ## Show this help
	@echo ""
	@echo "  Maestro — AI Project Planner + Agent Orchestrator"
	@echo ""
	@echo "  Usage: make <target> [ARGS=\"...\"]"
	@echo ""
	@echo "  Setup:"
	@echo "    install          Install Python dependencies (uv sync --all-extras)"
	@echo "    clean            Remove .venv, caches, and build artifacts"
	@echo ""
	@echo "  Quick start:"
	@echo "    up               Install deps, build frontend, start everything"
	@echo ""
	@echo "  Run:"
	@echo "    start            Start web UI + orchestrator daemon (default: port 8000)"
	@echo "    serve            Start web UI only (no orchestrator)"
	@echo "    run              Start orchestrator daemon only (no web UI)"
	@echo "    validate         Validate a workflow.yaml config"
	@echo ""
	@echo "  Frontend:"
	@echo "    frontend         Build frontend for production (served at :8000)"
	@echo "    frontend-dev     Start frontend dev server with hot reload (:5173)"
	@echo ""
	@echo "  Dev:"
	@echo "    test             Run all tests"
	@echo "    test-fast        Run unit tests only (< 5s)"
	@echo "    lint             Run ruff linter"
	@echo "    format           Auto-format with ruff"
	@echo "    snapshot-update  Update syrupy test snapshots"
	@echo ""
	@echo "  Examples:"
	@echo "    make start ARGS=\"--port 4200\""
	@echo "    make serve ARGS=\"--host 127.0.0.1\""
	@echo "    make validate ARGS=\"workflow.yaml\""
	@echo ""
