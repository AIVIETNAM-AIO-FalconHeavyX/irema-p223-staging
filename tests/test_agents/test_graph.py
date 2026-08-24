import pytest
from fastapi.testclient import TestClient

from src.agents.graph import agent
from src.main import app


@pytest.mark.asyncio
async def test_agent_basic_rag_flow():
    result = await agent.ainvoke(
        {
            "query": "Thời gian bảo hành pin LFP xe máy điện là bao nhiêu?",
            "raw_query": "Thời gian bảo hành pin LFP xe máy điện là bao nhiêu?",
            "user_role": "technician",
        }
    )
    assert "response" in result
    assert result.get("intent") in ["RAG_SEARCH", "GENERAL_QA", "TROUBLESHOOTING"]
    assert isinstance(result.get("citations"), list)


@pytest.mark.asyncio
async def test_agent_troubleshooting_flow():
    result = await agent.ainvoke(
        {
            "query": "Báo lỗi P01 quá nhiệt pin",
            "raw_query": "Báo lỗi P01 quá nhiệt pin",
            "user_role": "technician",
        }
    )
    assert "response" in result
    assert result.get("intent") == "TROUBLESHOOTING"


@pytest.mark.asyncio
async def test_agent_workflow_flow():
    result = await agent.ainvoke(
        {
            "query": "Hướng dẫn quy trình onboarding dành cho nhân viên bán hàng",
            "raw_query": "Hướng dẫn quy trình onboarding dành cho nhân viên bán hàng",
            "user_role": "sales",
        }
    )
    assert "response" in result
    assert result.get("intent") == "WORKFLOW"


@pytest.mark.asyncio
async def test_agent_escalation_flow():
    result = await agent.ainvoke(
        {
            "query": "Tôi muốn gặp IT support để tạo ticket hỗ trợ sự cố",
            "raw_query": "Tôi muốn gặp IT support để tạo ticket hỗ trợ sự cố",
            "user_role": "sales",
        }
    )
    assert "response" in result
    assert result.get("intent") == "CREATE_TICKET"
    assert result.get("needs_escalation") is True
    assert result.get("ticket_payload") is not None
    assert "TICK-" in result["ticket_payload"]["ticket_id"]


def test_chat_api_endpoint():
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Chính sách chiết khấu bán xe máy điện VinFast",
            "user_role": "sales",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "analysis" in data
    assert "citations" in data


@pytest.mark.asyncio
async def test_agent_no_info_found_citations():
    result = await agent.ainvoke(
        {
            "query": "Thời tiết hôm nay ở Hà Nội như thế nào?",
            "raw_query": "Thời tiết hôm nay ở Hà Nội như thế nào?",
            "user_role": "sales",
        }
    )
    assert "response" in result
    if "Không tìm thấy thông tin" in result["response"]:
        assert result.get("citations") == []


@pytest.mark.asyncio
async def test_agent_workflow_citations_accuracy():
    result = await agent.ainvoke(
        {
            "query": "Hướng dẫn quy trình onboarding dành cho nhân viên bán hàng",
            "raw_query": "Hướng dẫn quy trình onboarding dành cho nhân viên bán hàng",
            "user_role": "sales",
        }
    )
    assert result.get("intent") == "WORKFLOW"
    citations = result.get("citations", [])
    # Workflow citations should be reasonable in number
    assert len(citations) <= 5
