import pytest

from src.agents.nodes.rag_node import set_rag_ready
from src.services.s3_document_service import set_s3_ready


@pytest.mark.asyncio
async def test_liveness_probes(client):
    # Test /live
    res_live = await client.get("/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    # Test /health/live
    res_health_live = await client.get("/health/live")
    assert res_health_live.status_code == 200
    assert res_health_live.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_probes(client):
    # Case 1: When unready
    set_rag_ready(False)
    set_s3_ready(False)

    res_unready = await client.get("/ready")
    assert res_unready.status_code == 503
    assert res_unready.json()["status"] == "unready"
    assert res_unready.json()["rag_ready"] is False
    assert res_unready.json()["s3_ready"] is False

    res_health_unready = await client.get("/health/ready")
    assert res_health_unready.status_code == 503

    # Case 2: When ready
    set_rag_ready(True)
    set_s3_ready(True)

    res_ready = await client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"
    assert res_ready.json()["rag_ready"] is True
    assert res_ready.json()["s3_ready"] is True

    res_health_ready = await client.get("/health/ready")
    assert res_health_ready.status_code == 200


@pytest.mark.asyncio
async def test_general_health_endpoint(client):
    set_rag_ready(True)
    set_s3_ready(True)
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
