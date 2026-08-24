"""Langfuse Localhost Tracing Service for 100% On-Premise Observability."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.config import get_settings

logger = logging.getLogger(__name__)


def get_langfuse_handler(
    user_role: str = "sales",
    session_id: str | None = None,
    user_id: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Any | None:
    """
    Initialize and return a Langfuse CallbackHandler for LangGraph / LangChain tracing.
    Returns None if Langfuse is disabled or keys are missing.
    """
    settings = get_settings()

    if not settings.langfuse_enabled:
        return None

    host = settings.langfuse_host or os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
    public_key = settings.langfuse_public_key or os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = settings.langfuse_secret_key or os.environ.get("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        logger.debug("Langfuse keys not configured. Localhost tracing is inactive.")
        return None

    try:
        from langfuse.langchain import CallbackHandler

        merged_tags = ["production", "live_chat", user_role]
        if tags:
            merged_tags.extend(tags)

        handler = CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            session_id=session_id or "default_session",
            user_id=user_id or user_role,
            tags=list(set(merged_tags)),
            metadata=metadata or {},
        )
        return handler
    except Exception as e:
        logger.warning(f"Failed to initialize Langfuse CallbackHandler: {e}")
        return None
