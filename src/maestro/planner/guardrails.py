"""Input guardrails — validate and sanitize user input before it reaches the agent.

# See README: "Guardrails" — three lines of defence (Input layer)

Four-layer input validation, cheapest first:

1. **Length cap** — rejects inputs longer than MAX_INPUT_CHARS (regex, instant).
2. **Prompt injection detection** — catches override/jailbreak patterns (regex, instant).
3. **Profanity filter** — catches obvious abuse (regex, instant).
4. **Allowlist + LLM classifier** — allowlist passes known-good project inputs
   instantly (regex, free).  Only inputs that fail the allowlist go to a cheap
   LLM classifier (Haiku/gpt-4o-mini/Flash) for a RELEVANT/OFF_TOPIC check.
   Falls back to allowing the input on classifier failure — the system prompt
   is the safety net.
"""

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Length cap
# ---------------------------------------------------------------------------

MAX_INPUT_CHARS: int = 5_000
"""Maximum characters accepted per user input.

Generous enough for detailed project descriptions and multi-paragraph
answers, but prevents accidental pastes of entire files or deliberate
context-window flooding.
"""

# ---------------------------------------------------------------------------
# Prompt injection patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
        r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
        r"forget\s+(all\s+)?(your|previous|prior)\s+(instructions?|prompts?|rules?)",
        r"you\s+are\s+now\s+(a|an|the)\s+",
        r"new\s+instructions?\s*:",
        r"system\s*:\s*you\s+are",
        r"<\s*/?\s*system\s*>",
        r"\bact\s+as\s+(a|an|the)\s+(?!scrum|product|project)",
        r"override\s+(your|the|all)\s+(instructions?|prompts?|rules?|guidelines?)",
        r"pretend\s+(you\s+are|to\s+be)\s+",
    )
]

# ---------------------------------------------------------------------------
# Profanity — fast regex pre-check (no LLM call needed for obvious abuse)
# ---------------------------------------------------------------------------

_PROFANITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(f+u+c*k|sh[i1]+t|stfu|wtf)\b",
        r"\b(bitch|asshole|dickhead|bastard|dumbass|retard)\b",
        r"\b(dirty|filthy|nasty|naughty)\s+(boy|boii?|girl|bitch|slut|dog)\b",
        r"\b(suck\s*(my|it|this)|blow\s*me|eat\s*my|kiss\s*my\s*a)\b",
    )
]

# ---------------------------------------------------------------------------
# Allowlist — known-good patterns that skip the LLM classifier
# ---------------------------------------------------------------------------

# Short commands and questionnaire responses
_ALLOWLIST_EXACT: frozenset[str] = frozenset(
    {
        # Questionnaire commands
        "yes",
        "no",
        "y",
        "n",
        "skip",
        "defaults",
        "confirm",
        "back",
        "continue",
        "done",
        "ok",
        "sure",
        "start",
        "analyse",
        "analyze",
        "go",
        "proceed",
        "accept",
        "reject",
        "edit",
        "export",
        # Choice answers (numbers)
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        # Common short answers
        "none",
        "n/a",
        "na",
        "not sure",
        "not yet",
        "no idea",
        "i don't know",
        "idk",
        "tbd",
        "to be determined",
        "greenfield",
        "existing codebase",
        "hybrid",
        "monorepo",
        "multi-repo",
        "microservices",
        "monolith",
        "both",
        "jira",
        "markdown",
        # Sprint lengths
        "1 week",
        "2 weeks",
        "3 weeks",
        "4 weeks",
    }
)

# Patterns that indicate project-relevant content (case-insensitive).
# If ANY of these match, the input is considered relevant — instant pass.
_ALLOWLIST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        # --- Numbers and quantities ---
        r"\d+\s*(developer|engineer|dev|person|people|member|sprint|week|month|point|story)",
        r"\d+\s*(pts?|sp)\b",  # story points
        r"\b(team\s*(of|size|is)|velocity\s*(is|of|\d))",
        # --- Tech stack / languages / frameworks ---
        r"\b(python|java|javascript|typescript|go|golang|rust|ruby|php|swift|kotlin|c\+\+|c#|scala"
        r"|elixir|dart|perl|r\b|lua|haskell|clojure|erlang)\b",
        r"\b(react|angular|vue|svelte|next\.?js|nuxt|remix|gatsby|astro)\b",
        r"\b(node\.?js|express|fastapi|django|flask|rails|spring|laravel|nest\.?js|gin|fiber|echo)\b",
        r"\b(postgres|postgresql|mysql|mariadb|mongodb|redis|elasticsearch|dynamodb|sqlite|cassandra"
        r"|cockroachdb|supabase|firebase|neo4j|influxdb)\b",
        r"\b(aws|azure|gcp|google\s*cloud|heroku|vercel|netlify|cloudflare|digitalocean|linode)\b",
        r"\b(docker|kubernetes|k8s|terraform|ansible|pulumi|helm|argo|jenkins|circleci|github\s*actions"
        r"|gitlab\s*ci|azure\s*devops|bitbucket\s*pipelines)\b",
        r"\b(graphql|rest\s*api|grpc|websocket|mqtt|rabbitmq|kafka|nats|celery|sidekiq)\b",
        r"\b(tailwind|bootstrap|material\s*ui|chakra|styled|css|sass|less)\b",
        r"\b(prisma|sequelize|typeorm|sqlalchemy|hibernate|drizzle|knex)\b",
        r"\b(jest|pytest|junit|mocha|cypress|playwright|selenium|vitest|rspec)\b",
        r"\b(webpack|vite|esbuild|rollup|turbopack|parcel|babel)\b",
        r"\b(nginx|apache|caddy|traefik|envoy|haproxy)\b",
        r"\b(auth0|okta|keycloak|cognito|oauth|jwt|saml|sso|ldap)\b",
        r"\b(stripe|paypal|twilio|sendgrid|mailgun|slack|s3|sqs|sns|lambda)\b",
        r"\b(openai|anthropic|claude|gpt|llm|langchain|langgraph|hugging\s*face|ai\s*agent|ai\s*model|ai|ml"
        r"|machine\s*learning|deep\s*learning|neural|rag|embeddings?|vector\s*db|fine\s*tun)\b",
        r"\b(git|github|gitlab|bitbucket|azure\s*devops)\b",
        # --- Project / software terms ---
        r"\b(api|endpoint|route|controller|service|model|schema|migration|database|db)\b",
        r"\b(frontend|backend|fullstack|full\s*stack|microservices?|monolith|serverless)\b",
        r"\b(deploy|deployment|release|pipeline|ci/?cd|staging|production|dev\s*env)\b",
        r"\b(sprint|epic|story|task|backlog|kanban|scrum|agile|standup|retro)\b",
        r"\b(mvp|prototype|poc|proof\s*of\s*concept|beta|alpha|launch|milestone)\b",
        r"\b(feature|bug|fix|refactor|tech\s*debt|legacy|migrate|migration)\b",
        r"\b(component|module|package|library|plugin|extension|widget|hook)\b",
        r"\b(auth|login|signup|registration|user|admin|role|permission|dashboard)\b",
        r"\b(payment|checkout|cart|order|invoice|subscription|billing|notification)\b",
        r"\b(search|filter|sort|paginate|upload|download|import|export|sync)\b",
        r"\b(test|testing|unit\s*test|integration\s*test|e2e|coverage|qa|quality)\b",
        r"\b(security|encryption|ssl|tls|https|cors|csrf|xss|injection|vulnerability)\b",
        r"\b(cache|caching|cdn|performance|optimization|latency|throughput|scalab)\b",
        r"\b(monitoring|logging|alerting|observability|metrics|traces|datadog|grafana)\b",
        r"\b(repository|repo|branch|pull\s*request|pr|merge|commit|code\s*review)\b",
        r"\b(docker|container|image|volume|network|compose|swarm|pod|cluster)\b",
        r"\b(webhook|callback|event|queue|pubsub|message\s*broker|stream)\b",
        r"\b(mobile|ios|android|react\s*native|flutter|xamarin|cordova|expo)\b",
        r"\b(responsive|accessibility|a11y|i18n|localization|l10n|rtl)\b",
        r"\b(design|figma|sketch|wireframe|mockup|prototype|ui|ux)\b",
        r"\b(documentation|docs|readme|changelog|wiki|confluence|notion)\b",
        r"\b(stakeholder|client|customer|user|product\s*owner|po|manager|lead)\b",
        r"\b(estimate|complexity|risk|blocker|dependency|constraint|scope|deadline)\b",
        r"\b(greenfield|brownfield|existing\s*codebase|hybrid|rewrite|rebuild)\b",
        # --- Project intent verbs and general nouns ---
        r"\b(build|create|develop|implement|design|architect|ship|deliver|maintain|scale)\b",
        r"\b(app|application|website|web\s*app|system|tool|portal|platform|service|product)\b",
        r"\b(agent|bot|chatbot|automation|workflow|integration|connector|adapter|wrapper)\b",
        # --- Business / domain terms ---
        r"\b(b2b|b2c|saas|paas|iaas|enterprise|startup|platform|marketplace)\b",
        r"\b(ecommerce|e-commerce|fintech|healthtech|edtech|proptech|insuretech)\b",
        r"\b(crm|erp|cms|lms|hrms|pos|booking|reservation|inventory|logistics)\b",
        r"\b(onboarding|workflow|approval|compliance|audit|reporting|analytics)\b",
        r"\b(revenue|pricing|subscription|freemium|trial|quota|tenant|multi-tenant)\b",
        # --- URLs ---
        r"https?://",
        r"\b(github\.com|gitlab\.com|bitbucket\.org|dev\.azure\.com)\b",
        # --- File paths and extensions ---
        r"\b[\w/]+\.(py|js|ts|tsx|jsx|go|rs|rb|java|kt|cs|php|yaml|yml|json|toml|md)\b",
        # --- Timeline / deadline phrases ---
        r"\b(by|before|after|within|in)\s+\d+\s*(day|week|month|sprint|quarter)",
        r"\b(q[1-4]|h[12])\s*\d{0,4}\b",  # Q1 2025, H2, etc.
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
        r"\b(deadline|timeline|roadmap|eta|target\s*date|go\s*live|ship)\b",
        # --- Uncertainty / "I don't know" variations ---
        r"\b(not\s*sure|don'?t\s*know|no\s*idea|uncertain|unclear|tbd|undecided|maybe)\b",
        r"\b(haven'?t\s*decided|still\s*(deciding|figuring|working))\b",
        r"\b(no\s*(existing|known|specific|explicit|hard)|none\s*(yet|that|so\s*far))\b",
    )
]

# ---------------------------------------------------------------------------
# LLM off-topic classifier (only called when allowlist doesn't match)
# ---------------------------------------------------------------------------

_CLASSIFIER_MODELS: dict[str, str] = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
    "google": "gemini-2.0-flash",
}

_CLASSIFIER_PROMPT = """\
You are a relevance classifier for a project planning tool that creates \
epics, user stories, sprints, and tasks for software projects.

Classify this user input as RELEVANT or OFF_TOPIC.

RELEVANT — could be a project planning answer (description, tech, team, timeline, etc.):
"e-commerce platform" → RELEVANT
"we need it by March" → RELEVANT
"React and Python" → RELEVANT
"not sure yet" → RELEVANT
"we have 3 backend devs and 1 designer" → RELEVANT

OFF_TOPIC — clearly unrelated to software project planning:
"do you love me" → OFF_TOPIC
"tell me a joke" → OFF_TOPIC
"whats up you dirty boii" → OFF_TOPIC
"show me the future" → OFF_TOPIC
"what is the meaning of life" → OFF_TOPIC
"can you sing" → OFF_TOPIC
"who won the world cup" → OFF_TOPIC

Respond with exactly one word: RELEVANT or OFF_TOPIC"""

_OFFTOPIC_MAX_LEN = 200


def check_input_length(text: str) -> str | None:
    """Return an error message if *text* exceeds the length cap, else None."""
    if len(text) > MAX_INPUT_CHARS:
        return (
            f"Input too long ({len(text):,} chars). "
            f"Maximum is {MAX_INPUT_CHARS:,} characters — please shorten your response."
        )
    return None


def check_profanity(text: str) -> str | None:
    """Return a warning if *text* contains obvious profanity, else None."""
    for pattern in _PROFANITY_PATTERNS:
        if pattern.search(text):
            return (
                "I'm a project planning agent — I can help with epics, stories, sprints, and tasks. "
                "Please enter a project-related response."
            )
    return None


def _passes_allowlist(text: str) -> bool:
    """Return True if text matches a known-good project input pattern.

    Checks exact matches first (command words, numbers), then regex
    patterns for tech terms, project vocabulary, URLs, etc.
    """
    lowered = text.strip().lower()

    # Exact match — questionnaire commands, numbers, short answers
    if lowered in _ALLOWLIST_EXACT:
        return True

    # Pure numbers are always valid (team size, sprint count, points, etc.)
    if lowered.replace(".", "").replace(",", "").strip().isdigit():
        return True

    # Regex patterns — tech stack, project terms, URLs, timelines
    for pattern in _ALLOWLIST_PATTERNS:
        if pattern.search(text):
            return True

    return False


def check_off_topic(text: str) -> str | None:
    """Check input relevance: allowlist first, then LLM classifier if needed.

    Only checks short inputs (≤200 chars). Long inputs are assumed to be
    project descriptions. Returns a redirect message if off-topic, None if
    relevant. On classifier error, returns None (system prompt is fallback).
    """
    if len(text) > _OFFTOPIC_MAX_LEN:
        return None

    # Fast path — allowlist match means it's relevant, no LLM call needed
    if _passes_allowlist(text):
        return None

    # Slow path — input didn't match any known-good pattern, ask the LLM
    try:
        from maestro import config as _config_module
        from maestro.planner import llm as _llm_module

        provider = _config_module.get_llm_provider()
        model = _CLASSIFIER_MODELS.get(provider)
        llm = _llm_module.get_llm(model=model, temperature=0.0)
        # Disable retries — this is a non-critical guardrail; failing fast is
        # better than blocking the REPL for seconds on API overload (529).
        llm.max_retries = 0

        response = llm.invoke(f"{_CLASSIFIER_PROMPT}\n\nUser input: {text}")
        result = response.content.strip().upper()

        if "OFF_TOPIC" in result:
            return (
                "I'm a project planning agent — I can help with epics, stories, sprints, and tasks. "
                "Please enter a project-related response."
            )
    except Exception:
        logger.debug("Off-topic classifier failed, allowing input", exc_info=True)

    return None


def check_prompt_injection(text: str) -> str | None:
    """Return a warning message if *text* matches a known injection pattern, else None."""
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return "Your input looks like a prompt injection attempt and has been blocked. Please rephrase your answer."
    return None


def validate_input(text: str) -> str | None:
    """Run all input guardrails.  Returns the first error/warning, or None if clean.

    Order: length → injection → profanity (all regex, instant) → allowlist + LLM (last).
    """
    return check_input_length(text) or check_prompt_injection(text) or check_profanity(text) or check_off_topic(text)


# ---------------------------------------------------------------------------
# Output guardrails — programmatic validation of LLM-generated artifacts.
# ---------------------------------------------------------------------------

# See README: "Guardrails" — three lines of defence (Output layer)
#
# These validators run after the LLM generates stories and sprints.
# They catch structural issues that prompt enforcement alone can miss:
#   - Story format: persona/goal/benefit must all be non-empty
#   - AC coverage: each story should have happy + at least one negative/edge/error AC
#   - Sprint capacity: no sprint should exceed team velocity
#   - Scope creep: total story points vs. stated sprint count * velocity
#   - Unrealistic sprint loads: individual sprints packed to the limit
#
# Each function returns a list of warning strings (empty = all good).
# Warnings are displayed to the user after artifact rendering — they
# do NOT block the pipeline, since the LLM output may still be usable.

from maestro.planner.state import Sprint, UserStory

# ---------------------------------------------------------------------------
# Story format validation
# ---------------------------------------------------------------------------

# Minimum meaningful length for persona/goal/benefit fields.
_MIN_FIELD_LEN = 2


def validate_story_format(stories: list[UserStory]) -> list[str]:
    """Check that every story has non-trivial persona, goal, and benefit."""
    logger.debug("Validating story format for %d stories", len(stories))
    warnings: list[str] = []
    for s in stories:
        missing = []
        if len(s.persona.strip()) < _MIN_FIELD_LEN:
            missing.append("persona")
        if len(s.goal.strip()) < _MIN_FIELD_LEN:
            missing.append("goal")
        if len(s.benefit.strip()) < _MIN_FIELD_LEN:
            missing.append("benefit")
        if missing:
            warnings.append(f"{s.id}: missing or too short — {', '.join(missing)}")
    if warnings:
        logger.warning("Story format: %d issue(s) found", len(warnings))
    else:
        logger.debug("Story format: all %d stories passed", len(stories))
    return warnings


# ---------------------------------------------------------------------------
# Acceptance criteria coverage
# ---------------------------------------------------------------------------

# Keywords that suggest negative / edge / error scenarios in AC text.
_NEGATIVE_KEYWORDS = re.compile(
    r"\b(invalid|fail|error|denied|unauthorized|reject|missing|empty|exceed|timeout|unavailable|forbidden"
    r"|wrong|incorrect|expired|duplicate|overflow|malformed|corrupt)\b",
    re.IGNORECASE,
)


def validate_ac_coverage(stories: list[UserStory]) -> list[str]:
    """Check each story has >=2 ACs and at least one negative/edge case."""
    logger.debug("Validating AC coverage for %d stories", len(stories))
    warnings: list[str] = []
    for s in stories:
        acs = s.acceptance_criteria
        if len(acs) < 2:
            warnings.append(f"{s.id}: only {len(acs)} AC(s) — consider adding more scenarios")
            continue

        # Check if any AC covers a negative/edge case
        has_negative = any(_NEGATIVE_KEYWORDS.search(f"{ac.given} {ac.when} {ac.then}") for ac in acs)
        if not has_negative:
            warnings.append(f"{s.id}: all ACs appear to be happy-path — consider adding negative/edge cases")
    if warnings:
        logger.warning("AC coverage: %d issue(s) found", len(warnings))
    else:
        logger.debug("AC coverage: all %d stories passed", len(stories))
    return warnings


# ---------------------------------------------------------------------------
# Sprint capacity validation
# ---------------------------------------------------------------------------


def validate_sprint_capacity(sprints: list[Sprint], stories: list[UserStory], velocity: int) -> list[str]:
    """Check that no sprint exceeds team velocity."""
    logger.debug("Validating sprint capacity (%d sprints, velocity=%d)", len(sprints), velocity)
    warnings: list[str] = []
    if velocity <= 0:
        return warnings

    points_map = {s.id: s.story_points.value for s in stories}
    for sp in sprints:
        actual = sum(points_map.get(sid, 0) for sid in sp.story_ids)
        if actual > velocity:
            over = actual - velocity
            warnings.append(f"{sp.name}: {actual} pts exceeds velocity {velocity} by {over} pts")
    return warnings


# ---------------------------------------------------------------------------
# Scope vs. capacity check
# ---------------------------------------------------------------------------


def validate_scope_vs_capacity(
    sprints: list[Sprint],
    stories: list[UserStory],
    velocity: int,
) -> list[str]:
    """Flag when total scope significantly exceeds planned capacity."""
    warnings: list[str] = []
    if velocity <= 0 or not sprints:
        return warnings

    total_points = sum(s.story_points.value for s in stories)
    total_capacity = velocity * len(sprints)

    if total_points > total_capacity:
        over_pct = ((total_points - total_capacity) / total_capacity) * 100
        if over_pct > 10:
            warnings.append(
                f"Total scope ({total_points} pts) exceeds capacity "
                f"({len(sprints)} sprints × {velocity} pts = {total_capacity} pts) "
                f"by {over_pct:.0f}% — consider adding sprints or reducing scope"
            )
    return warnings


# ---------------------------------------------------------------------------
# Aggregate runner
# ---------------------------------------------------------------------------


def validate_output(
    stories: list[UserStory] | None = None,
    sprints: list[Sprint] | None = None,
    velocity: int = 0,
) -> list[str]:
    """Run all applicable output guardrails and return combined warnings."""
    logger.debug("Running output validation")
    warnings: list[str] = []
    if stories:
        warnings.extend(validate_story_format(stories))
        warnings.extend(validate_ac_coverage(stories))
    if sprints and stories:
        warnings.extend(validate_sprint_capacity(sprints, stories, velocity))
        warnings.extend(validate_scope_vs_capacity(sprints, stories, velocity))
    if warnings:
        logger.warning("Output validation: %d total warning(s)", len(warnings))
    else:
        logger.debug("Output validation: all checks passed")
    return warnings
