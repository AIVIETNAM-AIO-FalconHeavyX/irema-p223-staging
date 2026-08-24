"""Braintrust integration service for AI Tracing, Logging, and Observability."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

try:
    import braintrust  # type: ignore[import-untyped,import-not-found]
except ImportError:
    braintrust = None

from src.config import get_settings

logger = logging.getLogger(__name__)

_braintrust_logger = None


def get_braintrust_logger():
    """Initialize and return the global Braintrust logger instance."""
    global _braintrust_logger
    if _braintrust_logger is not None:
        return _braintrust_logger

    if braintrust is None:
        logger.debug("braintrust package is not installed. Tracing is disabled.")
        return None

    settings = get_settings()
    api_key = settings.braintrust_api_key or os.environ.get("BRAINTRUST_API_KEY")
    project = settings.braintrust_project_name or os.environ.get("BRAINTRUST_PROJECT_NAME", "p223-agent")

    if not api_key:
        logger.debug("BRAINTRUST_API_KEY is not set. Braintrust tracing is disabled.")
        return None

    try:
        _braintrust_logger = braintrust.init_logger(
            project=project,
            api_key=api_key,
        )
        logger.info(f"Braintrust initialized successfully for project '{project}'.")
        return _braintrust_logger
    except Exception as e:
        logger.warning(f"Failed to initialize Braintrust logger: {e}")
        return None


def log_chat_interaction(
    message: str,
    response: str,
    user_role: str = "sales",
    intent: str | None = None,
    citations: list[str] | None = None,
    analysis: str = "",
    needs_escalation: bool = False,
    duration_ms: float | None = None,
    session_id: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    """Auto-log real-time chatbot interactions into Braintrust live log stream."""
    bt_logger = get_braintrust_logger()
    if not bt_logger:
        return

    try:
        metadata = {
            "endpoint": "/api/v1/chat",
            "user_role": user_role,
            "intent": intent or "UNKNOWN",
            "citations_count": len(citations) if citations else 0,
            "citations": citations or [],
            "needs_escalation": needs_escalation,
            "session_id": session_id or "default_session",
            **(extra_metadata or {}),
        }
        if analysis:
            metadata["analysis"] = analysis[:500]

        metrics = {}
        if duration_ms is not None:
            metrics["duration_ms"] = round(duration_ms, 2)
            metrics["duration"] = round(duration_ms / 1000.0, 3)

        bt_logger.log(
            input={
                "message": message,
                "user_role": user_role,
            },
            output={
                "response": response,
                "intent": intent,
                "citations": citations or [],
                "needs_escalation": needs_escalation,
            },
            metadata=metadata,
            metrics=metrics,
            tags=["production", "chat", user_role],
        )
        logger.debug("Successfully logged chat interaction to Braintrust.")
    except Exception as e:
        logger.warning(f"Failed to log chat interaction to Braintrust: {e}")


def log_llm_call(
    input_text: str,
    output_text: str,
    metadata: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    span_name: str = "llm_completion",
) -> None:
    """Log an LLM interaction / agent step to Braintrust."""
    bt_logger = get_braintrust_logger()
    if not bt_logger:
        return

    try:
        bt_logger.log(
            input=input_text,
            output=output_text,
            metadata=metadata or {},
            metrics=metrics or {},
        )
    except Exception as e:
        logger.warning(f"Failed to log event to Braintrust: {e}")


def braintrust_traced(name: str | None = None) -> Callable:
    """Decorator to trace functions and agent steps in Braintrust."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            bt_logger = get_braintrust_logger()
            if not bt_logger:
                return func(*args, **kwargs)

            span_name = name or func.__name__
            try:
                with braintrust.traced(name=span_name) as span:
                    span.log(input={"args": str(args)[:500], "kwargs": str(kwargs)[:500]})
                    result = func(*args, **kwargs)
                    span.log(output=str(result)[:1000])
                    return result
            except Exception as e:
                logger.debug(f"Braintrust span error in {span_name}: {e}")
                return func(*args, **kwargs)

        return wrapper

    return decorator
