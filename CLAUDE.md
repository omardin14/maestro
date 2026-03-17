# CLAUDE.md

## Project

Maestro — Unified Scrum Planner + Agent Orchestrator. A single product with a web UI where users plan projects (epics → stories → tasks → sprints), export them as Linear issues, and an orchestrator daemon picks those issues up and autonomously works on them with Claude Code agents.

## Commands

```bash
make install              # Install uv + all dependencies
make test                 # Full test suite
make test-fast            # Unit tests only (< 5s)
make lint                 # Ruff linting
make format               # Ruff formatting
make serve                # Start web server (planner + dashboard UI)
make run                  # Start orchestrator daemon only
make start                # Start both web server + orchestrator
make validate             # Validate workflow.yaml config
make snapshot-update      # Update syrupy snapshots
uv run pytest tests/unit/planner/test_state.py -v          # Single test file
uv run pytest tests/unit/planner/test_state.py::TestFoo -v # Single test class
```

## Code Style

- Python 3.11+, ruff for linting/formatting (line-length 120)
- Imports sorted by ruff (isort rules: stdlib, third-party, local)
- Tests in `tests/`, source in `src/maestro/`

## Project Structure

```
src/maestro/
  __init__.py               # Package init, LangSmith noise suppression
  __main__.py               # python -m maestro
  cli.py                    # Unified CLI: serve, run, start, validate, export
  config.py                 # Shared config (env vars, API keys)
  models.py                 # Shared domain models (Issue, RunAttempt, RetryEntry)
  linear_client.py          # Linear GraphQL client

  planner/                  # From scrum-jira-agent
    state.py                # ScrumState, Epic, UserStory, Task, Sprint
    graph.py                # LangGraph graph factory
    nodes.py                # All pipeline nodes
    llm.py                  # LLM provider factory
    guardrails.py           # Input/output guardrails
    prompts/                # Prompt templates
    tools/                  # @tool functions (jira, github, azdo, confluence, calendar, llm)
    exporters/
      html.py               # HTML report
      markdown.py           # Markdown export
      linear.py             # Batch export plan → Linear issues

  runner/                   # From stokowski
    orchestrator.py         # Poll loop, dispatch, reconciliation, retry
    agent_runner.py         # Claude Code CLI subprocess + stream-json
    prompt_assembler.py     # Three-layer prompt (global + stage + lifecycle)
    tracking.py             # State comments on Linear for crash recovery
    workspace.py            # Per-issue workspace lifecycle + hooks
    workflow_config.py      # workflow.yaml parser + typed dataclasses
    supervisor.py           # asyncio supervisor (OTP-inspired)

  api/                      # Web layer
    app.py                  # FastAPI app factory
    ws.py                   # WebSocket connection manager
    planner_routes.py       # Planner REST + WS endpoints
    runner_routes.py        # Orchestrator REST + WS endpoints

frontend/                   # React SPA (Vite + TypeScript)

tests/
  unit/planner/             # Ported from scrum-jira-agent
  unit/runner/              # Orchestrator tests
  integration/              # API + WebSocket tests
  contract/                 # VCR cassettes for Linear
```

## Architecture

**Planner** (from scrum-jira-agent): LangGraph pipeline with 7 nodes (intake → analyzer → epics → stories → tasks → sprints → agent). Human-in-the-loop review gates after each generation node. Frozen dataclasses for artifacts.

**Runner** (from stokowski): Polls Linear for issues, dispatches Claude Code CLI subprocesses, manages state machine transitions (agent/gate/terminal). Three-layer prompt assembly. Crash recovery via structured Linear comments.

**Bridge**: Planner generates plans → exports as Linear issues → Runner picks them up autonomously.

## Git Conventions

- Commit messages: lowercase imperative (e.g. "add streaming output", "fix retry logic")
- Include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` on AI-assisted commits
