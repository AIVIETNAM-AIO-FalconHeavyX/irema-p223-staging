"""Feedback API routes — POST /feedback, GET /feedback/stats."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.db import get_db
from src.db.models import ChatFeedback, FeedbackRating, User

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class FeedbackRequest(BaseModel):
    query: str = Field(..., description="Câu hỏi của user")
    response: str = Field(..., description="Câu trả lời AI")
    intent: str | None = Field(default=None, description="Intent được phân loại")
    citations: list[str] = Field(default_factory=list, description="Danh sách tài liệu trích dẫn")
    rerank_scores: list[float] = Field(default_factory=list, description="Rerank scores của từng chunk")
    rag_confidence: float | None = Field(default=None, description="RAG confidence score (0-1)")
    rating: str = Field(..., description="'up' | 'neutral' | 'down'")


class FeedbackResponse(BaseModel):
    id: int
    created_at: datetime
    rating: str
    message: str = "Cảm ơn phản hồi của bạn!"


class FeedbackStats(BaseModel):
    total: int
    up: int
    neutral: int
    down: int
    up_pct: float
    down_pct: float
    by_intent: dict[str, dict[str, int]]
    low_quality_queries: list[dict]  # Câu hỏi hay bị ↓ nhất


# ---------------------------------------------------------------------------
# POST /feedback
# ---------------------------------------------------------------------------


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    """Ghi nhận đánh giá ↑/−/↓ từ user cho một câu trả lời AI."""
    try:
        rating_enum = FeedbackRating(payload.rating)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"rating phải là 'up', 'neutral' hoặc 'down'. Nhận được: '{payload.rating}'",
        )

    feedback = ChatFeedback(
        user_id=current_user.id,
        user_role=current_user.role.value,
        query=payload.query,
        response=payload.response[:5000],  # Giới hạn để tránh DB quá lớn
        intent=payload.intent,
        citations=json.dumps(payload.citations, ensure_ascii=False) if payload.citations else None,
        rerank_scores=json.dumps(payload.rerank_scores) if payload.rerank_scores else None,
        rag_confidence=payload.rag_confidence,
        rating=rating_enum,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    logger.info(
        "Feedback recorded: id=%d user=%s intent=%s rating=%s",
        feedback.id,
        current_user.email,
        payload.intent,
        payload.rating,
    )

    return FeedbackResponse(
        id=feedback.id,
        created_at=feedback.created_at,
        rating=payload.rating,
    )


# ---------------------------------------------------------------------------
# GET /feedback/stats — Manager/Owner only
# ---------------------------------------------------------------------------


@router.get("/feedback/stats", response_model=FeedbackStats)
def get_feedback_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackStats:
    """Thống kê feedback theo intent và câu hỏi hay bị ↓. Chỉ dành cho Manager/Owner/Vinfast."""
    allowed_roles = {"manager", "owner", "vinfast"}
    if current_user.role.value not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Manager/Owner mới được xem thống kê feedback.",
        )

    since = datetime.now(UTC) - timedelta(days=days)
    base_q = db.query(ChatFeedback).filter(ChatFeedback.created_at >= since)

    total = base_q.count()
    up = base_q.filter(ChatFeedback.rating == FeedbackRating.up).count()
    neutral = base_q.filter(ChatFeedback.rating == FeedbackRating.neutral).count()
    down = base_q.filter(ChatFeedback.rating == FeedbackRating.down).count()

    up_pct = round(up / total * 100, 1) if total else 0.0
    down_pct = round(down / total * 100, 1) if total else 0.0

    # Thống kê theo intent
    by_intent: dict[str, dict[str, int]] = {}
    rows = (
        db.query(ChatFeedback.intent, ChatFeedback.rating, func.count())
        .filter(ChatFeedback.created_at >= since)
        .group_by(ChatFeedback.intent, ChatFeedback.rating)
        .all()
    )
    for intent_val, rating_val, count_val in rows:
        key = intent_val or "UNKNOWN"
        if key not in by_intent:
            by_intent[key] = {"up": 0, "neutral": 0, "down": 0}
        by_intent[key][rating_val] = count_val

    # Top 10 câu hỏi hay bị ↓ nhất
    low_quality = (
        db.query(ChatFeedback.query, ChatFeedback.intent, ChatFeedback.rag_confidence, ChatFeedback.created_at)
        .filter(ChatFeedback.created_at >= since, ChatFeedback.rating == FeedbackRating.down)
        .order_by(ChatFeedback.created_at.desc())
        .limit(10)
        .all()
    )
    low_quality_queries = [
        {
            "query": row.query[:200],
            "intent": row.intent,
            "rag_confidence": row.rag_confidence,
            "created_at": row.created_at.isoformat(),
        }
        for row in low_quality
    ]

    return FeedbackStats(
        total=total,
        up=up,
        neutral=neutral,
        down=down,
        up_pct=up_pct,
        down_pct=down_pct,
        by_intent=by_intent,
        low_quality_queries=low_quality_queries,
    )
