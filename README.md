# Maestro

AI-powered project planner and autonomous executor. Plan projects into epics, stories, tasks, and sprints through a guided web UI, then let AI agents execute the work autonomously.

## What it does

1. **Plan** — A guided intake wizard asks about your project, then an AI pipeline generates epics, user stories, tasks, acceptance criteria, and sprint plans. You review and edit each step.
2. **Export** — Push the plan to your tracker (Jira, Linear, GitHub Issues, Azure DevOps) as a hierarchy of issues, each with AI prompts baked into the description.
3. **Execute** — An orchestrator daemon polls your tracker, picks up tasks, spins up Claude Code agents in isolated workspaces, and works through them autonomously with a configurable state machine (investigate → review → implement → code review → merge → done).

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node.js 18+** and **npm**
- **Anthropic API key**

## Quick start

```bash
# 1. Copy env file and add your API key
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY=sk-ant-...

# 2. Install everything, build frontend, and start
make up
```

Open http://localhost:8000 — you'll see the Planner tab where you can start a new planning session.

## Commands

Run `make` to see all available commands.

```
  Setup:
    up               Install deps, build frontend, start everything
    install          Install Python dependencies
    frontend         Build frontend for production
    clean            Remove .venv, caches, and build artifacts

  Run:
    start            Start web UI + orchestrator daemon
    serve            Start web UI only (no orchestrator)
    run              Start orchestrator daemon only (no web UI)

  Dev:
    test             Run all tests
    test-fast        Run unit tests only (< 5s)
    lint             Run ruff linter
    format           Auto-format with ruff
    frontend-dev     Start frontend dev server with hot reload (:5173)

  Examples:
    make up
    make start ARGS="--port 4200"
    make validate ARGS="workflow.yaml"
```

## Configuration

### Environment variables (.env)

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `LINEAR_API_KEY` | For orchestrator | Linear API key for issue tracking |
| `LLM_PROVIDER` | No | `anthropic` (default), `openai`, or `google` |
| `LLM_MODEL` | No | Override the default model |
| `GITHUB_TOKEN` | No | GitHub integration |
| `JIRA_BASE_URL` | No | Jira instance URL |
| `JIRA_EMAIL` | No | Jira account email |
| `JIRA_API_TOKEN` | No | Jira API token |

See `.env.example` for the full list.

### Workflow configuration (workflow.yaml)

The orchestrator uses a `workflow.yaml` to define the state machine, prompts, hooks, and tracker mappings. See `workflow.example.yaml` for a fully commented example.

```yaml
tracker:
  kind: linear                    # linear, jira, github, azdo
  project_slug: "your-project"

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
                   │  intake      │   │  poll tracker   │
                   │  → analyze   │   │  → dispatch     │
                   │  → epics     │   │  → Claude Code  │
                   │  → stories   │   │  → state mgmt   │
                   │  → tasks     │   │  → retry        │
                   │  → sprints   │   │                 │
                   └──────┬───────┘   └────────┬────────┘
                          │                    │
                          ▼                    ▼
                  ┌──────────────┐      ┌─────────────┐
                  │   Tracker    │◄────►│ Claude Code │
                  │ Jira/Linear/ │      │   Agents    │
                  │ GitHub/AzDo  │      └─────────────┘
                  └──────────────┘
```

**Planner**: LangGraph pipeline with 7 nodes. Guided 30-question intake, then generates epics, stories, tasks, acceptance criteria, and sprint plans. Human-in-the-loop review gates let you accept, edit, or reject each output.

**Runner**: Polls your tracker for "Todo" issues, dispatches Claude Code CLI subprocesses in isolated workspaces, and manages state machine transitions. Three-layer prompt assembly (global + stage + lifecycle context). Crash recovery via structured comments on issues.

**The bridge**: The planner exports its output as tracker issues with AI prompts in the description. The orchestrator picks those up and feeds the prompts to Claude Code agents.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/planner/sessions` | Create planning session |
| `GET` | `/api/planner/sessions` | List sessions |
| `GET` | `/api/planner/sessions/{id}` | Get session state |
| `POST` | `/api/planner/sessions/{id}/message` | Send user input |
| `POST` | `/api/planner/sessions/{id}/review` | Accept/edit/reject |
| `POST` | `/api/planner/sessions/{id}/export` | Export session |
| `WS` | `/ws/planner/{session_id}` | Real-time pipeline events |
| `GET` | `/api/runner/state` | Orchestrator snapshot |
| `POST` | `/api/runner/start` | Start orchestrator |
| `POST` | `/api/runner/stop` | Stop orchestrator |
| `WS` | `/ws/runner` | Live state changes |

## License

Private.
