from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.asyncio
async def test_rag_node_does_not_expose_raw_context_when_llm_fails(monkeypatch):
    import src.agents.nodes.rag_node as rag_module

    chunk = {
        "content": "INTERNAL DOCUMENT CONTENT THAT MUST NOT BE RETURNED RAW",
        "metadata": {
            "document": "Sales Process.pdf",
            "role": "sales",
            "section": "Process",
        },
        "rrf_score": 0.8,
        "rerank_score": 0.9,
    }
    retriever = Mock()
    retriever.search.return_value = [chunk]
    reranker = Mock()
    reranker.rerank.return_value = [chunk]
    failing_llm = Mock()
    failing_llm.ainvoke = AsyncMock(side_effect=RuntimeError("provider unavailable"))

    monkeypatch.setattr(rag_module, "get_retriever", Mock(return_value=retriever))
    monkeypatch.setattr(rag_module, "get_reranker", Mock(return_value=reranker))
    monkeypatch.setattr(rag_module, "get_llm", Mock(return_value=failing_llm))
    monkeypatch.setattr(
        rag_module,
        "get_settings",
        Mock(
            return_value=SimpleNamespace(
                openai_api_key="configured",
                google_api_key="",
                access_scope_mapping={"sales": ["sales", "general"]},
            )
        ),
    )

    result = await rag_module.rag_node(
        {
            "raw_query": "What is the sales process?",
            "query": "What is the sales process?",
            "user_role": "sales",
        }
    )

    assert result["context"] == rag_module.LLM_UNAVAILABLE_MESSAGE
    assert "INTERNAL DOCUMENT CONTENT" not in result["context"]
    assert result["citations"] == []
    assert result["needs_escalation"] is True
    assert result["rag_confidence"] == 0.2
