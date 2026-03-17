# Maestro — TODO & Roadmap

> Unified AI Product for Managing and Executing Projects

---

## Completed

### Phase 0: Scaffolding
- [x] `pyproject.toml` — hatchling build, Python 3.11+, uv, entry point `maestro`
- [x] `Makefile` — install, test, test-fast, lint, format, serve, run, start, validate, clean
- [x] Ruff config (line-length 120, isort rules)
- [x] Pytest config with markers (`slow`, `eval`, `vcr`, `smoke`)
- [x] `.env.example` with all required keys
- [x] `.pre-commit-config.yaml` (trailing whitespace, ruff)
- [x] `.gitignore` for Python, frontend, IDE, OS
- [x] `src/maestro/__init__.py` + `__main__.py`
- [x] `CLAUDE.md` for the unified project
- [x] Package init files for all subpackages

### Phase 1: Planner Domain Logic (ported from scrum-jira-agent)
- [x] `state.py` — ScrumState, all enums, frozen dataclasses (598 lines)
- [x] `nodes.py` — All pipeline nodes (6,324 lines)
- [x] `graph.py` — LangGraph graph factory (297 lines, 9 nodes + conditional edges)
- [x] `llm.py` — Multi-provider LLM factory (Anthropic, OpenAI, Google)
- [x] `guardrails.py` — Merged input + output guardrails
- [x] `prompts/` — 8 prompt modules
- [x] `tools/` — 8 tool modules (jira, github, azure_devops, confluence, calendar, codebase, llm_tools)
- [x] `exporters/html.py` — Self-contained HTML report generator (738 lines)
- [x] `config.py` — Shared env/API key management
- [x] Ported 44 test files from scrum-jira-agent → `tests/unit/planner/`
- [x] Ported test fixtures and helpers
- [x] All 1,587 tests passing

### Phase 2: Orchestrator Logic (ported from stokowski)
- [x] `orchestrator.py` — Poll loop, dispatch, state machine, retry (1,179 lines)
- [x] `agent_runner.py` — Claude Code CLI subprocess + NDJSON stream (489 lines)
- [x] `prompt_assembler.py` — Three-layer prompt assembly with Jinja2 (306 lines)
- [x] `tracking.py` — State comments on Linear for crash recovery (165 lines)
- [x] `workspace.py` — Per-issue workspace lifecycle + hooks (102 lines)
- [x] `workflow_config.py` — YAML config parser + typed dataclasses (482 lines)
- [x] `models.py` — Shared domain models (Issue, RunAttempt, RetryEntry)
- [x] `linear_client.py` — Async Linear GraphQL client with httpx (363 lines)
- [x] `workflow.example.yaml` — Example 8-state workflow config

### Phase 3: FastAPI Backend + WebSocket
- [x] `app.py` — FastAPI app factory with CORS, static files, health endpoint
- [x] `ws.py` — WebSocket ConnectionManager with room-based subscriptions
- [x] Planner REST endpoints (sessions CRUD, message, review, export)
- [x] Planner WebSocket endpoint (`/ws/planner/{session_id}`)
- [x] Runner REST endpoints (state, issue detail, refresh, start/stop)
- [x] Runner WebSocket endpoint (`/ws/runner`)

### Phase 4–5: React Frontend
- [x] Vite + TypeScript setup with API/WS proxy
- [x] Design system — dark theme (#080808), amber accents, IBM Plex Mono
- [x] StatusBadge component with state-based colors
- [x] Header — "MAESTRO" brand, Planner/Dashboard nav tabs
- [x] Typed REST client for all endpoints
- [x] Auto-reconnecting WebSocket hook
- [x] PlannerPage — session creation, state management, intake/artifact routing
- [x] IntakeWizard — 7-phase progress bar, question cards, text input
- [x] ArtifactViewer — Epics, stories, tasks, sprints display + review gate
- [x] DashboardPage — Metrics cards, session table, retry queue
- [x] React Router with `/planner` and `/dashboard` routes
- [x] Dark theme global styles

### Phase 10: CLI Entry Point
- [x] `maestro serve` — start web server
- [x] `maestro run` — orchestrator daemon only
- [x] `maestro start` — web server + orchestrator
- [x] `maestro validate` — validate workflow.yaml
- [x] `maestro export` — export saved session
- [x] Global `.env` loading + Rich logging

---

## In Progress / Planned

### Phase 5b: Missing Planner Features (gaps from scrum-jira-agent port)
_Functionality that existed in scrum-jira-agent but was lost or left incomplete during the port._

**Critical:**
- [ ] **Session persistence** — Replace in-memory session storage with SQLite + LangGraph checkpointing
  - Port `persistence.py` (28KB) and `sessions.py` (25KB) from scrum-jira-agent
  - Wire into planner API routes (currently has `# TODO: replace with persistent storage`)
  - Sessions survive server restarts and crashes
- [ ] **Session resume** — Resume a previous planning session from where it left off
  - `GET /api/planner/sessions` returns saved sessions from DB
  - `POST /api/planner/sessions/{id}/message` picks up mid-pipeline
- [ ] **Wire up CLI export** — `maestro export` is a stub; connect it to the existing `exporters/html.py`
- [ ] **Questionnaire import/export** — Port `questionnaire_io.py` for offline planning
  - `POST /api/planner/sessions/{id}/import-questionnaire` (upload Markdown)
  - `GET /api/planner/questionnaire-template` (download blank template)
  - CLI: `maestro import-questionnaire <file>` and `maestro export-questionnaire`

**Nice-to-have:**
- [ ] **Dry-run mode** — Run the full pipeline with fake delays and no LLM calls (for demos/testing)
  - API: `POST /api/planner/sessions` with `{"dry_run": true}`
  - CLI: `maestro serve --dry-run`
- [ ] **Auto-accept mode** — Skip all review gates and generate a full plan end-to-end
  - API: `POST /api/planner/sessions` with `{"auto_accept": true}`
  - Useful for batch/scripted planning runs
- [ ] **Quick intake mode** — 17 essential questions instead of the full 26
  - API: `POST /api/planner/sessions` with `{"intake_mode": "quick"}`
- [ ] **Setup wizard** — First-run guided API key validation in web UI
  - Check for required env vars on startup, show setup page if missing

### Phase 5c: Test Gaps
_Tests that existed in scrum-jira-agent but weren't ported._

- [ ] **Integration tests** (~330KB across 10 files):
  - CLI end-to-end tests
  - Full pipeline graph runs
  - Graph topology validation
  - Multi-node flow tests
  - ReAct loop tests
- [ ] **Contract tests** (6 files) — Recorded API response tests:
  - Jira, GitHub, Azure DevOps, Confluence, LLM provider contracts
  - Schema validation tests
- [ ] **Golden dataset evaluators** (3 files) — Deterministic LLM output quality checks
- [ ] **Token budget regression** — `test_token_budgets.py` catches prompt size inflation in CI
- [ ] **Planner API integration tests** — New tests for the web API layer (sessions, messages, review, export)
- [ ] **WebSocket integration tests** — Test real-time event streaming during pipeline execution

### Phase 6: Tracker Abstraction + The Bridge
_Make the orchestrator tracker-agnostic so it works with Linear, Jira, GitHub Issues, or Azure DevOps — not just Linear._

- [ ] Define `Tracker` protocol/ABC (`runner/tracker.py`):
  - `poll_issues(state) → list[Issue]`
  - `move_issue(issue_id, from_state, to_state)`
  - `post_comment(issue_id, body)`
  - `fetch_issue(issue_id) → Issue`
  - `create_issue(title, description, parent_id, labels, ...) → issue_id`
- [ ] Refactor `linear_client.py` → implement `LinearTracker(Tracker)`
- [ ] Create `JiraTracker(Tracker)` — wraps existing Jira tools (jira.py) for orchestrator use
- [ ] Create `GitHubTracker(Tracker)` — poll GitHub Issues, post comments, move via labels/projects
- [ ] Create `AzDoTracker(Tracker)` — poll Azure DevOps work items, move via states
- [ ] Update `workflow_config.py` — `tracker.kind` selects which implementation (`linear`, `jira`, `github`, `azdo`)
- [ ] Update orchestrator to use `Tracker` interface instead of calling `LinearClient` directly
- [ ] Planner export uses the same abstraction — export to whichever tracker is configured
- [ ] Add Linear create mutations to `LinearTracker`:
  - `create_issue(title, description, team_id, state_id, priority, label_ids, parent_id)`
  - `create_label(name, team_id)`
  - `fetch_teams()` and `fetch_states(team_id)`
- [ ] Create `planner/tools/linear.py` — LangChain @tool functions:
  - `linear_create_epic`, `linear_create_story`, `linear_create_task`
- [ ] Create `planner/exporters/linear.py` — batch export:
  - Epics → parent issues (label: "epic")
  - Stories → sub-issues under epics (with story points, acceptance criteria)
  - Tasks → sub-issues under stories (AI prompts in description)
  - All created in "Todo" state for orchestrator pickup
  - Return mapping: internal artifact IDs → Linear issue IDs
- [ ] Add `linear_epic_keys` / `linear_story_keys` to ScrumState
- [ ] End-to-end test: planner → export to Linear → verify issues via API

### Phase 7: Supervisor + Fault Tolerance (OTP-inspired)
- [ ] `supervisor.py` — AgentSupervisor managing asyncio child tasks
  - Restart strategy with exponential backoff
  - Max restart intensity (N in T seconds → stop, like OTP)
  - Graceful shutdown with configurable timeout
  - Health monitoring: last heartbeat per child, kill stalled workers
  - `on_child_exit(issue_id, status, error)` callback
- [ ] Replace bare `asyncio.create_task()` in orchestrator with supervisor
- [ ] Wire `on_child_exit` to retry logic and WebSocket broadcast
- [ ] Process-level supervision docs (systemd, launchd, Docker healthcheck)

### Phase 8: SSH Remote Workers (from symphony)
- [ ] `ssh_runner.py` — SSH-wrapped subprocess execution
  - `run(host, command)` — single command
  - `start_streaming(host, command)` — long-running with output streaming
  - Support `host:port` and `MAESTRO_SSH_CONFIG`
- [ ] Extend `workflow_config.py` with `workers` section
- [ ] Extend orchestrator dispatch to route to remote workers
  - Least-loaded worker selection
  - Remote workspace creation, Claude Code execution, output streaming
- [ ] Worker health checks (SSH ping) in supervisor

### Phase 9: Token Accounting + Budgets (from symphony)
- [ ] `token_accounting.py` — TokenLedger
  - Per-session and aggregate counters
  - Rate limit tracking from Claude Code events
  - Time-windowed usage (tokens/minute, tokens/hour)
  - Budget alerts at threshold %, stop at max
- [ ] Extend `workflow_config.py` with `budget` section
- [ ] Integrate with orchestrator dispatch (pause when limits approached)
- [ ] WebSocket broadcast for live token updates
- [ ] Token sparkline data endpoint for dashboard charts

### Phase 10b: Bidirectional Tracker Sync
_Keep two trackers in sync — e.g. Jira as the team's source of truth, Linear as the agent execution layer._

- [ ] Webhook receivers for each tracker:
  - `POST /api/webhooks/jira` — Jira webhook (issue updated, status changed, comment added)
  - `POST /api/webhooks/linear` — Linear webhook (issue updated, state changed, comment added)
  - `POST /api/webhooks/github` — GitHub webhook (issue/project events)
  - `POST /api/webhooks/azdo` — Azure DevOps Service Hooks (work item updated, state changed, comment added)
- [ ] `SyncEngine` — maps events between trackers:
  - Field mapping config: which fields sync (status, assignee, labels, comments, priority)
  - State mapping: e.g. Jira "In Progress" ↔ Linear "In Progress" (configurable per project)
  - Conflict resolution: last-write-wins with configurable priority (e.g. "Jira wins on status, Linear wins on agent comments")
  - Deduplication: idempotency keys to prevent infinite sync loops
- [ ] Extend `workflow_config.py` with `sync` section:
  ```yaml
  sync:
    primary: jira          # source of truth for human changes
    agent_tracker: linear  # where orchestrator runs agents
    field_map:
      status: bidirectional
      comments: bidirectional
      priority: primary_to_agent
      labels: primary_to_agent
  ```
- [ ] Mirror planner exports: create in primary tracker, auto-create in agent tracker
- [ ] Sync agent completion back: orchestrator marks "Done" in Linear → status synced to Jira
- [ ] Comment mirroring: agent progress comments on Linear appear on the Jira ticket
- [ ] Dashboard view showing sync status and any conflicts

### Phase 11: Polish + Testing
- [ ] Comprehensive orchestrator unit tests
- [ ] End-to-end: plan → export → orchestrator picks up → agent runs → state transitions
- [ ] Frontend: loading states, error boundaries, toast notifications
- [ ] Frontend: responsive layout (desktop-first, tablet-friendly)
- [ ] Frontend: keyboard shortcuts (Ctrl+Enter submit, Escape cancel)
- [ ] Example `workflow.yaml` + prompt files for a complete setup

---

## Future: AI Product Vision

The features below extend Maestro from a developer tool into a full AI product management platform.

### Intelligent Planning

- [ ] **AI project estimation** — Train on historical velocity data to predict sprint capacity and delivery dates with confidence intervals
- [ ] **Smart dependency detection** — Automatically identify task dependencies from descriptions and acceptance criteria; build a DAG and flag circular dependencies
- [ ] **Risk scoring** — ML model that flags stories likely to slip based on complexity signals (# of integrations, ambiguous criteria, cross-team dependencies)
- [ ] **Requirement gap analysis** — LLM reviews generated stories against the original project description and highlights missing coverage
- [ ] **Automated acceptance criteria** — Generate Given/When/Then criteria from story descriptions using domain-specific LLM fine-tuning
- [ ] **Multi-project portfolio view** — Plan and track multiple projects; AI recommends resource allocation across projects
- [ ] **Natural language re-planning** — "Move the auth stories to sprint 3 and add 2 more points of capacity" → AI adjusts the plan

### Autonomous Execution

- [ ] **Self-healing agents** — When an agent fails, AI analyzes the error, adjusts the prompt/approach, and retries without human intervention
- [ ] **Parallel agent execution** — Run multiple non-dependent tasks concurrently across worker pool; auto-detect when tasks can be parallelized
- [ ] **AI code review gate** — Before human review, an AI reviewer checks the PR for bugs, style issues, test coverage, and security vulnerabilities
- [ ] **Test generation** — Agent automatically writes unit/integration tests for code it produces; validates tests pass before marking task complete
- [ ] **Incremental context building** — Each agent session builds on previous context; completed tasks inform subsequent task prompts
- [ ] **Multi-repo orchestration** — Single plan that spans multiple repositories; agents check out the right repo per task
- [ ] **Rollback on failure** — If an agent's PR breaks CI, automatically revert and re-queue with enriched error context

### Learning & Feedback Loop

- [ ] **Velocity learning** — Track actual vs. estimated story points over time; use this to calibrate future estimates
- [ ] **Prompt optimization** — A/B test different prompt strategies per task type; track success rates and auto-select best performers
- [ ] **Post-mortem analysis** — After each sprint, AI generates a retrospective: what was estimated vs. actual, common failure patterns, suggested process improvements
- [ ] **Agent skill profiles** — Track which types of tasks agents succeed/fail at; route tasks to the best-fit prompt/model combination
- [ ] **Human feedback ingestion** — When a human edits AI-generated code or rejects a plan, feed that signal back to improve future generations

### Collaboration & Integration

- [ ] **Slack/Teams bot** — "@maestro plan a new auth service" kicks off planning; status updates posted to channels
- [ ] **GitHub Issues / Jira Cloud sync** — Bidirectional sync: changes in Linear/Jira/GitHub reflect in Maestro and vice versa
- [ ] **PR auto-linking** — Agent-created PRs automatically linked to the originating task with full traceability
- [ ] **Stakeholder reports** — Auto-generate weekly status emails/Slack digests from sprint progress data
- [ ] **Multi-user sessions** — Multiple team members collaborate on the same planning session in real-time (CRDT-based conflict resolution)
- [ ] **Role-based access** — Product managers see planning views; engineers see execution dashboards; leads see portfolio views
- [ ] **Approval workflows** — Configurable approval chains: PM approves plan → Tech Lead approves architecture → agents execute

### Observability & Analytics

- [ ] **Execution timeline** — Gantt-style view of agent execution: when each task started, how long it ran, where it blocked
- [ ] **Cost dashboard** — Real-time spend tracking per project/sprint/task (LLM tokens + compute + API calls)
- [ ] **Quality metrics** — Track PR approval rates, CI pass rates, code coverage delta, lines of code per task
- [ ] **Bottleneck detection** — AI identifies which gate reviews are slowest, which task types take longest, where the pipeline stalls
- [ ] **Custom alerts** — "Notify me if any agent runs longer than 30 minutes" or "Alert if daily token spend exceeds $50"

### Platform & Extensibility

- [ ] **Plugin system** — Third-party tools (Figma, Notion, Confluence, custom APIs) as pluggable @tool functions
- [ ] **Custom workflow states** — Users define their own state machines beyond the default implement → review → done
- [ ] **Template library** — Pre-built workflow templates: "microservice", "mobile app", "data pipeline", "infrastructure"
- [ ] **Webhook API** — External systems trigger plans or receive execution events via webhooks
- [ ] **Multi-model support** — Route different task types to different LLMs (Claude for code, GPT for docs, Gemini for analysis)
- [ ] **Self-hosted / Cloud** — Package as Docker Compose for self-hosted; offer managed cloud version with team billing
- [ ] **Audit log** — Every AI decision, human override, and state transition logged for compliance and debugging

### Advanced AI Capabilities

- [ ] **Codebase understanding** — Before planning, AI indexes the existing codebase to generate context-aware tasks that reference actual files, functions, and patterns
- [ ] **Architecture advisor** — AI suggests architectural patterns based on project requirements (e.g., "this project needs a message queue for the async workflows")
- [ ] **Technical debt tracking** — AI identifies tech debt during execution and creates follow-up issues automatically
- [ ] **Documentation generation** — After task completion, auto-generate API docs, architecture decision records, and runbooks
- [ ] **Security scanning** — Integrated SAST/DAST: AI reviews generated code for OWASP Top 10 vulnerabilities before PR creation
- [ ] **Migration assistant** — "Migrate this Express app to FastAPI" → AI generates a full migration plan with ordered tasks and rollback steps
