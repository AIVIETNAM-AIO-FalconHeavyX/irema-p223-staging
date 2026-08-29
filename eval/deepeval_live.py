"""Run DeepEval against a deployed VF AI chat API.

This runner is intentionally separate from the application runtime. It sends
only the read-only ground-truth prompts and keeps credentials/tokens in memory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_DATASET = ROOT / "retrieval_debugger" / "ground_truth.json"
DEFAULT_JUDGE_MODEL = "gpt-4o-mini"
ROLE_ALIASES = {
    "sale": "sales",
    "sales": "sales",
    "accountant": "accounting",
    "accounting": "accounting",
    "ktv": "technician",
    "technician": "technician",
    "general": "general",
}
REQUIRED_ROLES = ("sales", "technician", "accounting", "general")
SIDE_EFFECT_INTENTS = {"CREATE_TICKET"}
REFUSAL_MARKERS = (
    "không tìm thấy",
    "khÃ´ng tÃ¬m tháº¥y",
    "không có thông tin",
    "khÃ´ng cÃ³ thÃ´ng tin",
    "không hỗ trợ",
    "khÃ´ng há»— trá»£",
)


class LiveEvaluationError(RuntimeError):
    """Raised for configuration or transport failures before evaluation ends."""


def normalize_role(role: str) -> str:
    """Normalize dataset/API role aliases to the dataset vocabulary."""
    normalized = ROLE_ALIASES.get(role.strip().casefold())
    if normalized is None:
        raise LiveEvaluationError(f"Unsupported evaluation role: {role!r}")
    return normalized


def load_dataset(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise LiveEvaluationError(f"Dataset not found: {dataset_path}")
    try:
        data = json.loads(dataset_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveEvaluationError(f"Unable to load dataset {dataset_path}: {exc}") from exc
    if not isinstance(data, list):
        raise LiveEvaluationError("Evaluation dataset must contain a JSON list")
    selected = data[:limit] if limit is not None else data
    for item in selected:
        if not isinstance(item, dict) or not item.get("query"):
            raise LiveEvaluationError("Every evaluation case must contain a query")
        normalize_role(str(item.get("role", "general")))
    return selected


def credential_env_names(role: str) -> tuple[str, str]:
    role_name = normalize_role(role).upper()
    return f"DEEPEVAL_{role_name}_EMAIL", f"DEEPEVAL_{role_name}_PASSWORD"


def load_credentials(role: str, environ: dict[str, str] | None = None) -> tuple[str, str]:
    env = environ if environ is not None else os.environ
    email_key, password_key = credential_env_names(role)
    email = env.get(email_key, "").strip()
    password = env.get(password_key, "")
    if not email or not password:
        raise LiveEvaluationError(f"Missing {email_key} and/or {password_key}")
    return email, password


def _role_from_user(user: dict[str, Any]) -> str:
    value = user.get("role")
    if not isinstance(value, str):
        raise LiveEvaluationError("Login response did not contain user.role")
    return normalize_role(value)


def _request_json(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = client.request(method, url, json=payload, headers=headers)
        response.raise_for_status()
        body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise LiveEvaluationError(f"Request failed for {url}: {exc}") from exc
    if not isinstance(body, dict):
        raise LiveEvaluationError(f"Expected a JSON object from {url}")
    return body


def login_role(client: httpx.Client, base_url: str, role: str) -> str:
    expected_role = normalize_role(role)
    email, password = load_credentials(expected_role)
    result = _request_json(
        client,
        "POST",
        f"{base_url}/api/v1/auth/login",
        payload={"email": email, "password": password},
    )
    token = result.get("access_token")
    if not isinstance(token, str) or not token:
        raise LiveEvaluationError(f"Login for role {expected_role} returned no access token")
    actual_role = _role_from_user(result.get("user") or {})
    if actual_role != expected_role:
        raise LiveEvaluationError(
            f"Credential role mismatch: expected {expected_role}, API returned {actual_role}"
        )
    return token


def extract_contexts(response: dict[str, Any]) -> list[str]:
    contexts: list[str] = []
    for document in response.get("retrieved_docs") or []:
        if isinstance(document, dict):
            content = document.get("content_preview", "")
            if isinstance(content, str) and content.strip():
                contexts.append(content.strip())
    return contexts


def keyword_coverage(answer: str, keywords: list[str] | None) -> float:
    if isinstance(keywords, str):
        keywords = [keywords]
    expected = [str(keyword).casefold().strip() for keyword in (keywords or []) if str(keyword).strip()]
    if not expected:
        return 1.0
    actual = answer.casefold()
    return sum(keyword in actual for keyword in expected) / len(expected)


def refusal_check(answer: str, expected_document_ids: list[str] | None) -> bool | None:
    if expected_document_ids:
        return None
    lowered = answer.casefold()
    return any(marker in lowered for marker in REFUSAL_MARKERS)


def safety_signals(response: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    intent = response.get("intent")
    if isinstance(intent, str) and intent in SIDE_EFFECT_INTENTS:
        signals.append(f"intent:{intent}")
    if response.get("needs_escalation") is True:
        signals.append("needs_escalation:true")
    if response.get("ticket_payload") is not None:
        signals.append("ticket_payload:present")
    return signals


def validate_chat_response(response: dict[str, Any]) -> None:
    """Validate the stable fields required by the public chat contract."""
    if not isinstance(response.get("response"), str):
        raise LiveEvaluationError("Chat response field 'response' must be a string")
    if response.get("citations") is not None and not isinstance(response["citations"], list):
        raise LiveEvaluationError("Chat response field 'citations' must be a list")
    if response.get("retrieved_docs") is not None and not isinstance(response["retrieved_docs"], list):
        raise LiveEvaluationError("Chat response field 'retrieved_docs' must be a list")


def validate_judge_model(model_name: str, api_key: str | None = None) -> None:
    """Validate the exact OpenAI model identifier before creating chat sessions."""
    key = api_key or os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise LiveEvaluationError("OPENAI_API_KEY is required for judge-model validation")
    try:
        from openai import OpenAI

        OpenAI(api_key=key).models.retrieve(model_name)
    except Exception as exc:
        raise LiveEvaluationError(
            f"Judge model {model_name!r} is unavailable or could not be validated: {exc}"
        ) from exc


def validate_target_environment(
    client: httpx.Client,
    base_url: str,
    requested_environment: str,
    allow_production: bool,
) -> dict[str, Any]:
    """Check the deployed server before creating conversations."""
    health = _request_json(client, "GET", f"{base_url}/health/live")
    actual_environment = health.get("env")
    if actual_environment == "production" and (
        requested_environment != "production" or not allow_production
    ):
        raise LiveEvaluationError(
            "The target reports env=production. Use --environment production "
            "--allow-production only after confirming this is the intended target."
        )
    return health


def build_metrics(model_name: str) -> dict[str, Any]:
    """Build DeepEval metrics lazily so normal tests do not require DeepEval."""
    try:
        from deepeval.metrics import (
            AnswerRelevancyMetric,
            ContextualRecallMetric,
            ContextualRelevancyMetric,
            FaithfulnessMetric,
        )
    except ImportError as exc:
        raise LiveEvaluationError(
            "DeepEval is not installed. Install evaluation dependencies with "
            "pip install -r requirements-eval.txt"
        ) from exc

    return {
        "answer_relevancy": AnswerRelevancyMetric(model=model_name, include_reason=True),
        "faithfulness": FaithfulnessMetric(model=model_name, include_reason=True),
        "contextual_relevancy": ContextualRelevancyMetric(model=model_name, include_reason=True),
        "contextual_recall": ContextualRecallMetric(model=model_name, include_reason=True),
    }


def measure_metrics(
    *,
    metrics: dict[str, Any],
    query: str,
    answer: str,
    expected_answer: str,
    contexts: list[str],
    out_of_scope: bool,
) -> dict[str, Any]:
    try:
        from deepeval.test_case import LLMTestCase
    except ImportError as exc:
        raise LiveEvaluationError("DeepEval is not installed") from exc

    test_case = LLMTestCase(
        input=query,
        actual_output=answer,
        expected_output=expected_answer,
        retrieval_context=contexts,
    )
    selected = ["answer_relevancy"]
    if contexts:
        selected.append("faithfulness")
        if not out_of_scope:
            selected.extend(("contextual_relevancy", "contextual_recall"))

    result: dict[str, Any] = {}
    for name in selected:
        metric = metrics[name]
        try:
            metric.measure(test_case)
            result[name] = {
                "score": float(metric.score) if metric.score is not None else None,
                "reason": metric.reason,
                "success": metric.success,
            }
        except Exception as exc:
            result[name] = {"score": None, "reason": None, "success": False, "error": str(exc)}
    return result


def aggregate_scores(cases: list[dict[str, Any]]) -> dict[str, float | None]:
    values: defaultdict[str, list[float]] = defaultdict(list)
    for case in cases:
        for name, metric in (case.get("deepeval_metrics") or {}).items():
            score = metric.get("score")
            if isinstance(score, (int, float)):
                values[name].append(float(score))
    return {
        name: round(sum(scores) / len(scores), 4) if scores else None
        for name, scores in sorted(values.items())
    }


def run_live_evaluation(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if args.environment == "production" and not args.allow_production:
        raise LiveEvaluationError("Production evaluation requires --allow-production")
    if not args.api_url:
        raise LiveEvaluationError("Provide --api-url or DEEPEVAL_API_URL")

    dataset = load_dataset(args.dataset, args.limit)
    judge_model = args.judge_model or os.getenv("DEEPEVAL_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
    validate_judge_model(judge_model)
    metrics = build_metrics(judge_model)
    base_url = args.api_url.rstrip("/")
    run_id = uuid.uuid4().hex
    started = datetime.now(UTC)
    tokens: dict[str, str] = {}
    cases: list[dict[str, Any]] = []
    aborted_for_safety = False

    with httpx.Client(timeout=args.timeout) as client:
        validate_target_environment(
            client,
            base_url,
            args.environment,
            args.allow_production,
        )
        for item in dataset:
            role = normalize_role(str(item.get("role", "general")))
            case_started = time.perf_counter()
            case: dict[str, Any] = {
                "query_id": item.get("query_id", ""),
                "role": role,
                "query": item["query"],
                "conversation_id": f"deepeval-{run_id}-{item.get('query_id') or uuid.uuid4().hex[:8]}",
                "status": "error",
            }
            try:
                if aborted_for_safety:
                    case["status"] = "skipped_after_safety_abort"
                    cases.append(case)
                    continue
                if role not in tokens:
                    tokens[role] = login_role(client, base_url, role)
                response = _request_json(
                    client,
                    "POST",
                    f"{base_url}/api/v1/chat",
                    payload={"message": item["query"], "conversation_id": case["conversation_id"]},
                    token=tokens[role],
                )
                validate_chat_response(response)
                answer = response["response"]
                contexts = extract_contexts(response)
                expected_docs = item.get("expected_document_id") or []
                if isinstance(expected_docs, str):
                    expected_docs = [expected_docs]
                signals = safety_signals(response)
                refusal_detected = refusal_check(answer, expected_docs)
                deterministic_failures: list[str] = []
                if not answer.strip():
                    deterministic_failures.append("empty_answer")
                if expected_docs and not response.get("citations"):
                    deterministic_failures.append("missing_citations")
                if not expected_docs and refusal_detected is not True:
                    deterministic_failures.append("missing_refusal")
                case.update(
                    {
                        "status": "passed_api",
                        "answer": answer,
                        "intent": response.get("intent"),
                        "citations": response.get("citations") or [],
                        "citation_present": bool(response.get("citations")),
                        "retrieved_context": contexts,
                        "keyword_coverage": keyword_coverage(answer, item.get("expected_keywords")),
                        "refusal_detected": refusal_detected,
                        "deterministic_failures": deterministic_failures,
                        "safety_signals": signals,
                    }
                )
                if signals:
                    aborted_for_safety = True
                    case["status"] = "unsafe_side_effect_signal"
                else:
                    case["deepeval_metrics"] = measure_metrics(
                        metrics=metrics,
                        query=item["query"],
                        answer=answer,
                        expected_answer=str(item.get("expected_answer", "")),
                        contexts=contexts,
                        out_of_scope=not bool(expected_docs),
                    )
            except LiveEvaluationError as exc:
                case["error"] = str(exc)
            finally:
                case["latency_ms"] = round((time.perf_counter() - case_started) * 1000, 2)
                cases.append(case)
                if args.request_delay > 0 and not aborted_for_safety:
                    time.sleep(args.request_delay)

    metric_averages = aggregate_scores(cases)
    available_scores = [score for score in metric_averages.values() if score is not None]
    quality_score = round(sum(available_scores) / len(available_scores), 4) if available_scores else None
    api_failures = sum(1 for case in cases if case["status"] == "error")
    report = {
        "run_id": run_id,
        "started_at": started.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "environment": args.environment,
        "api_url": base_url,
        "judge_model": judge_model,
        "dataset": str(Path(args.dataset)),
        "n_cases": len(cases),
        "metric_averages": metric_averages,
        "quality_score": quality_score,
        "api_failures": api_failures,
        "deterministic_failures": sum(bool(case.get("deterministic_failures")) for case in cases),
        "unsafe_side_effect_cases": sum(case["status"] == "unsafe_side_effect_signal" for case in cases),
        "aborted_for_safety": aborted_for_safety,
        "cases": cases,
    }
    output_path = (
        Path(args.output_json)
        if args.output_json
        else ROOT
        / "eval"
        / "results"
        / f"deepeval_live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DeepEval report saved -> {output_path}")

    exit_code = 0
    if (
        api_failures
        or aborted_for_safety
        or quality_score is None
        or quality_score < args.min_quality_score
        or report["deterministic_failures"]
    ):
        exit_code = 1
    return report, exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run live DeepEval against the VF AI chat API.")
    parser.add_argument(
        "--api-url",
        default=os.getenv("DEEPEVAL_API_URL"),
        help="Staging/production API base URL",
    )
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET), help="Ground-truth JSON path")
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only the first N cases")
    parser.add_argument("--judge-model", default=None, help="Exact OpenAI judge model identifier")
    parser.add_argument("--output-json", default=None, help="Output report path")
    parser.add_argument("--request-delay", type=float, default=0.5, help="Seconds between chat requests")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout in seconds")
    parser.add_argument(
        "--min-quality-score",
        type=float,
        default=float(os.getenv("DEEPEVAL_MIN_QUALITY_SCORE", "0.7")),
    )
    parser.add_argument("--environment", choices=("staging", "production"), default="staging")
    parser.add_argument(
        "--allow-production",
        action="store_true",
        help="Required safety acknowledgement for production",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        _, exit_code = run_live_evaluation(args)
        return exit_code
    except LiveEvaluationError as exc:
        print(f"DeepEval preflight failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
