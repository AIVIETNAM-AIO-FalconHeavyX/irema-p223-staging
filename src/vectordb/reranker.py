from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)

COHERE_RERANK_URL = "https://api.cohere.com/v2/rerank"


class RerankerService:
    """Rerank retrieved chunks with Cohere and fall back to retrieval scores."""

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        request_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.rerank_model_name
        self.api_key = settings.cohere_api_key if api_key is None else api_key
        self.settings = settings
        self._request_fn = request_fn or self._request

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            COHERE_RERANK_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Client-Name": "p223-onboarding-agent",
            },
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _fallback(candidates: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        return sorted(
            (candidate.copy() for candidate in candidates),
            key=lambda item: item.get("rrf_score", item.get("score", 0.0)),
            reverse=True,
        )[:top_k]

    def rerank(
        self,
        query_text: str,
        candidates: list[dict[str, Any]],
        top_k: int = 5,
        min_score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        if not candidates or top_k <= 0:
            return []

        if not self.api_key:
            logger.warning("COHERE_API_KEY is not configured; using retrieval-score fallback.")
            return self._fallback(candidates, top_k)

        payload = {
            "model": self.model_name,
            "query": query_text,
            "documents": [candidate.get("content", "") for candidate in candidates],
            "top_n": min(top_k, len(candidates)),
        }

        try:
            response = self._request_fn(payload)
            results = response.get("results")
            if not isinstance(results, list) or not results:
                raise ValueError("Cohere response did not contain ranked results")
            threshold = self.settings.reranker_min_score if min_score_threshold is None else min_score_threshold
            ranked: list[dict[str, Any]] = []
            for result in results:
                index = int(result["index"])
                if index < 0 or index >= len(candidates):
                    continue
                score = float(result["relevance_score"])
                if score < threshold:
                    continue
                candidate = candidates[index].copy()
                candidate["rerank_score"] = score
                ranked.append(candidate)
            return ranked
        except (httpx.HTTPError, KeyError, TypeError, ValueError, RuntimeError) as exc:
            logger.warning("Cohere reranking failed (%s); using retrieval-score fallback.", exc)
            return self._fallback(candidates, top_k)
