import pytest
from httpx import AsyncClient

from src.db import SessionLocal
from src.db.models import ChatFeedback, FeedbackRating


async def _get_token(client: AsyncClient, email: str = "thehung@vinfast.vn", password: str = "12345678") -> str:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_feedback_submit_unauthorized(client: AsyncClient):
    res = await client.post(
        "/api/v1/feedback",
        json={
            "query": "Test query",
            "response": "Test response",
            "rating": "up",
        },
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_feedback_submit_valid(client: AsyncClient):
    token = await _get_token(client, email="thehung@vinfast.vn")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "query": "Hướng dẫn đăng nhập DMS",
        "response": "Để đăng nhập DMS: 1) Bước 1...",
        "intent": "RAG_SEARCH",
        "citations": ["01. Hướng dẫn đăng nhập DMS"],
        "rerank_scores": [8.4, 7.1],
        "rag_confidence": 0.92,
        "rating": "up",
    }
    res = await client.post("/api/v1/feedback", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["rating"] == "up"
    assert "id" in data
    assert data["message"] == "Cảm ơn phản hồi của bạn!"

    # Verify directly in DB
    db = SessionLocal()
    try:
        fb = db.query(ChatFeedback).filter(ChatFeedback.id == data["id"]).first()
        assert fb is not None
        assert fb.rating == FeedbackRating.up
        assert fb.query == payload["query"]
        assert fb.intent == payload["intent"]
    finally:
        db.close()


@pytest.mark.asyncio
async def test_feedback_submit_invalid_rating(client: AsyncClient):
    token = await _get_token(client, email="thehung@vinfast.vn")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "query": "Test query",
        "response": "Test response",
        "rating": "invalid_rating",
    }
    res = await client.post("/api/v1/feedback", json=payload, headers=headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_feedback_stats_authorized(client: AsyncClient):
    token = await _get_token(client, email="quanly@vinfast.vn")  # manager
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/feedback/stats", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "up" in data
    assert "neutral" in data
    assert "down" in data
    assert "by_intent" in data
    assert "low_quality_queries" in data


@pytest.mark.asyncio
async def test_feedback_stats_forbidden_for_regular_role(client: AsyncClient):
    token = await _get_token(client, email="sales@vinfast.vn")  # sale role
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/feedback/stats", headers=headers)
    assert res.status_code == 403
