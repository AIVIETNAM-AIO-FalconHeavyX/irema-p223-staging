from __future__ import annotations

import json
from argparse import Namespace

import pytest

from eval.deepeval_live import (
    LiveEvaluationError,
    aggregate_scores,
    build_parser,
    credential_env_names,
    extract_contexts,
    keyword_coverage,
    load_credentials,
    load_dataset,
    normalize_role,
    refusal_check,
    safety_signals,
    validate_chat_response,
    validate_judge_model,
    validate_target_environment,
)


def test_normalize_role_aliases() -> None:
    assert normalize_role("sale") == "sales"
    assert normalize_role("KTV") == "technician"
    assert credential_env_names("accountant") == ("DEEPEVAL_ACCOUNTING_EMAIL", "DEEPEVAL_ACCOUNTING_PASSWORD")


def test_missing_role_credentials_fail() -> None:
    with pytest.raises(LiveEvaluationError):
        load_credentials("sales", {})


def test_load_dataset_limit_and_validation(tmp_path) -> None:
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps([{"query": "q1", "role": "sale"}, {"query": "q2", "role": "general"}]), encoding="utf-8")
    assert len(load_dataset(path, limit=1)) == 1


def test_context_and_deterministic_checks() -> None:
    response = {
        "retrieved_docs": [{"content_preview": "A context"}, {"content_preview": "  "}],
        "intent": "RAG_SEARCH",
    }
    assert extract_contexts(response) == ["A context"]
    assert keyword_coverage("Pin LFP bảo hành 8 năm", ["pin lfp", "8 năm"]) == 1.0
    assert refusal_check("Không tìm thấy thông tin phù hợp", []) is True
    assert safety_signals(response) == []
    assert safety_signals({"intent": "CREATE_TICKET", "needs_escalation": True}) == [
        "intent:CREATE_TICKET",
        "needs_escalation:true",
    ]


def test_chat_response_schema_validation() -> None:
    validate_chat_response({"response": "ok", "citations": [], "retrieved_docs": []})
    with pytest.raises(LiveEvaluationError, match="citations"):
        validate_chat_response({"response": "ok", "citations": "bad"})


def test_aggregate_scores() -> None:
    cases = [
        {"deepeval_metrics": {"answer_relevancy": {"score": 0.8}}},
        {"deepeval_metrics": {"answer_relevancy": {"score": 1.0}}},
    ]
    assert aggregate_scores(cases) == {"answer_relevancy": 0.9}


def test_production_requires_explicit_flag(monkeypatch) -> None:
    from eval import deepeval_live

    args = Namespace(
        environment="production",
        allow_production=False,
        api_url="https://example.test",
        dataset="missing.json",
        limit=None,
        judge_model="gpt-4o-mini",
        output_json=None,
        request_delay=0,
        timeout=1,
        min_quality_score=0.7,
    )
    with pytest.raises(LiveEvaluationError, match="allow-production"):
        deepeval_live.run_live_evaluation(args)


def test_model_preflight_requires_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LiveEvaluationError, match="OPENAI_API_KEY"):
        validate_judge_model("gpt-5.6-sol")


def test_target_environment_rejects_production_without_acknowledgement() -> None:
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "alive", "env": "production"}

    class FakeClient:
        def request(self, *_args, **_kwargs):
            return FakeResponse()

    with pytest.raises(LiveEvaluationError, match="env=production"):
        validate_target_environment(FakeClient(), "https://example.test", "staging", False)


def test_parser_defaults_to_staging() -> None:
    args = build_parser().parse_args([])
    assert args.environment == "staging"
    assert args.judge_model is None
