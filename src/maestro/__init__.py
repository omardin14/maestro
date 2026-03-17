"""Maestro — Unified Scrum Planner + Agent Orchestrator."""

import logging
import warnings

# Suppress LangChain's Pydantic V1 compatibility warning on Python 3.14+.
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality", category=UserWarning)


class _LangSmithRateLimitFilter(logging.Filter):
    """Block LangSmith 429 messages and auto-disable tracing when rate-limited."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "429" in msg or "Rate limit" in msg or "LangSmithRateLimitError" in msg:
            try:
                from maestro.config import disable_langsmith_tracing

                disable_langsmith_tracing()
            except Exception:
                pass
            return False
        return True


class _SilentHandler(logging.Handler):
    """No-op handler that participates in filter checks."""

    def emit(self, record: logging.LogRecord) -> None:
        pass


_ls_handler = _SilentHandler()
_ls_handler.addFilter(_LangSmithRateLimitFilter())
_ls_logger = logging.getLogger("langsmith")
_ls_logger.addHandler(_ls_handler)
_ls_logger.propagate = False

__version__ = "0.1.0"
