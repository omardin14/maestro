# Maestro

AI-powered project planner and autonomous executor. Plan projects into epics, stories, tasks, and sprints through a guided web UI, then let AI agents execute the work autonomously.

## What it does

1. **Plan** — A guided intake wizard asks about your project, then an AI pipeline generates epics, user stories, tasks, acceptance criteria, and sprint plans. You review and edit each step.
2. **Export** — Push the plan to Linear as a hierarchy of issues (epics → stories → tasks), each with AI prompts baked into the description.
3. **Execute** — An orchestrator daemon polls Linear, picks up tasks, spins up Claude Code agents in isolated workspaces, and works through them autonomously with a configurable state machine (investigate → review → implement → code review → merge → done).

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Node.js 18+** and **npm** — for the frontend
- **Anthropic API key** — required for the AI planner and agents

## Quick start

```bash
# 1. Clone and enter the project
cd maestro

# 2. Copy env file and add your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 3. Install Python dependencies
make install

# 4. Install and build the frontend
cd frontend && npm install && npm run build && cd ..

# 5. Start everything
make start
# Opens on http://localhost:8000
```

Then open http://localhost:8000 — you'll see the Planner tab where you can start a new planning session.

## Commands

### Running Maestro

```bash
# Start web UI + orchestrator daemon (the default)
make start

# Start web UI only (planner, no autonomous agents)
make serve

# Start orchestrator daemon only (no web UI)
make run

# With custom port/host
make serve ARGS="--port 4200 --host 127.0.0.1"

# Validate a workflow config without running anything
make validate ARGS="workflow.yaml"
```

### Development

```bash
# Install all dependencies (Python + dev extras)
make install

# Run all tests
make test

# Run unit tests only (fast, < 5s)
make test-fast

# Run a specific test file
uv run pytest tests/unit/planner/test_state.py -v

# Lint
make lint

# Format
make format

# Update snapshot tests
make snapshot-update

# Clean build artifacts
make clean
```

### Frontend development

```bash
cd frontend

# Install dependencies
npm install

# Dev server with hot reload (proxies API to localhost:8000)
npm run dev

# Production build (output goes to frontend/dist/, served by FastAPI)
npm run build
```

When running the frontend dev server (`npm run dev`), it starts on http://localhost:5173 and proxies `/api` and `/ws` requests to the backend on port 8000. So you need the backend running too:

```bash
# Terminal 1: backend
make serve

# Terminal 2: frontend dev server
cd frontend && npm run dev
```

## Configuration

### Environment variables (.env)

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `LINEAR_API_KEY` | For orchestrator | Linear API key for issue tracking |
| `LLM_PROVIDER` | No | `anthropic` (default), `openai`, or `google` |
| `LLM_MODEL` | No | Override the default model |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `GOOGLE_API_KEY` | If using Google | Google AI API key |
| `LANGSMITH_TRACING` | No | Set `true` to enable LangSmith tracing |
| `LANGSMITH_API_KEY` | If tracing | LangSmith API key |
| `GITHUB_TOKEN` | No | For GitHub integration tools |
| `JIRA_BASE_URL` | No | Jira instance URL |
| `JIRA_EMAIL` | No | Jira account email |
| `JIRA_API_TOKEN` | No | Jira API token |

### Workflow configuration (workflow.yaml)

The orchestrator daemon is configured by a `workflow.yaml` file that defines the state machine, prompts, hooks, and Linear mappings. See `workflow.example.yaml` for a fully commented example.

Key sections:

```yaml
# What Linear project to poll
tracker:
  kind: linear
  project_slug: "your-project-slug"

# Map Linear states to lifecycle roles
linear_states:
  todo: "Todo"
  active: "In Progress"
  review: "Human Review"
  gate_approved: "Gate Approved"
  rework: "Rework"
  terminal: [Done, Closed, Cancelled]

# Define the state machine
states:
  investigate:
    type: agent
    prompt: prompts/investigate.md
    transitions:
      complete: review
  review:
    type: gate
    rework_to: investigate
    transitions:
      approve: implement
  implement:
    type: agent
    prompt: prompts/implement.md
    transitions:
      complete: done
  done:
    type: terminal
```

## Architecture

```
                    ┌─────────────────────────────────┐
                    │           Web UI (React)         │
                    │  ┌─────────────┬───────────────┐ │
                    │  │   Planner   │   Dashboard   │ │
                    │  │   Wizard    │   Live View   │ │
                    │  └──────┬──────┴───────┬───────┘ │
                    └─────────┼──────────────┼─────────┘
                         REST + WS      REST + WS
                    ┌─────────┼──────────────┼─────────┐
                    │         FastAPI Backend           │
                    │  ┌──────┴──────┐ ┌─────┴───────┐ │
                    │  │   Planner   │ │   Runner    │ │
                    │  │   Routes    │ │   Routes    │ │
                    │  └──────┬──────┘ └─────┬───────┘ │
                    └─────────┼──────────────┼─────────┘
                              │              │
                   ┌──────────┴───┐   ┌──────┴──────────┐
                   │   LangGraph   │   │  Orchestrator   │
                   │   Pipeline    │   │  Daemon         │
                   │              │   │                 │
                   │  intake      │   │  poll Linear    │
                   │  → analyze   │   │  → dispatch     │
                   │  → epics     │   │  → Claude Code  │
                   │  → stories   │   │  → state mgmt   │
                   │  → tasks     │   │  → retry        │
                   │  → sprints   │   │                 │
                   └──────┬───────┘   └────────┬────────┘
                          │                    │
                          ▼                    ▼
                    ┌────────────┐      ┌─────────────┐
                    │   Linear   │◄────►│ Claude Code │
                    │   Issues   │      │   Agents    │
                    └────────────┘      └─────────────┘
```

**Planner** (from scrum-jira-agent): LangGraph pipeline with 7 nodes. Walks you through a 30-question intake, analyzes the project, and generates artifacts. Human-in-the-loop review gates let you accept, edit, or reject each output.

**Runner** (from stokowski): Polls Linear for "Todo" issues, dispatches Claude Code CLI subprocesses in isolated git worktrees, and manages state machine transitions. Three-layer prompt assembly (global + stage + lifecycle context). Crash recovery via structured comments on Linear issues.

**The bridge**: The planner exports its output as Linear issues with AI prompts in the description. The orchestrator picks those issues up and feeds the prompts to Claude Code agents.

## API endpoints

### Planner

| Method | Path | Description |
|---|---|---|
| POST | `/api/planner/sessions` | Create a new planning session |
| GET | `/api/planner/sessions` | List all sessions |
| GET | `/api/planner/sessions/{id}` | Get session state |
| POST | `/api/planner/sessions/{id}/message` | Send user input to the pipeline |
| POST | `/api/planner/sessions/{id}/review` | Submit accept/edit/reject |
| POST | `/api/planner/sessions/{id}/export` | Export session (linear/html/markdown) |
| DELETE | `/api/planner/sessions/{id}` | Delete a session |
| WS | `/ws/planner/{session_id}` | Real-time pipeline events |

### Runner

| Method | Path | Description |
|---|---|---|
| GET | `/api/runner/state` | Orchestrator state snapshot |
| GET | `/api/runner/issues/{id}` | Single issue detail |
| POST | `/api/runner/refresh` | Trigger immediate poll |
| POST | `/api/runner/start` | Start orchestrator daemon |
| POST | `/api/runner/stop` | Stop orchestrator daemon |
| WS | `/ws/runner` | Live state change events |

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |

## Project structure

```
maestro/
  src/maestro/
    cli.py                    # CLI: serve, run, start, validate, export
    config.py                 # Shared env/API key config
    models.py                 # Domain models (Issue, RunAttempt, RetryEntry)
    linear_client.py          # Linear GraphQL client
    planner/                  # AI planning pipeline
      state.py                # ScrumState, Epic, UserStory, Task, Sprint
      graph.py                # LangGraph graph factory
      nodes.py                # Pipeline node functions
      llm.py                  # Multi-provider LLM factory
      guardrails.py           # Input/output validation
      prompts/                # Prompt templates
      tools/                  # LangChain @tool functions
      exporters/              # HTML, Markdown, Linear export
    runner/                   # Autonomous orchestrator
      orchestrator.py         # Poll loop, dispatch, retry
      agent_runner.py         # Claude Code subprocess management
      prompt_assembler.py     # Three-layer prompt assembly
      tracking.py             # Linear comment-based crash recovery
      workspace.py            # Per-issue workspace lifecycle
      workflow_config.py      # workflow.yaml parser
    api/                      # FastAPI web layer
      app.py                  # App factory
      ws.py                   # WebSocket manager
      planner_routes.py       # Planner endpoints
      runner_routes.py        # Runner endpoints
  frontend/                   # React + TypeScript SPA
  tests/                      # Unit, integration, contract tests
```

## License

Private.
