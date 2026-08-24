"""Structured correlation logger for RAG retrieval and debugging."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class RetrievalItemLog:
    document_id: str
    score: float
    rank: int
    title: str
    section: str = ""
    role_scope: str = "general"
    content_preview: str = ""
    raw_content: str = ""


@dataclass
class TestCaseLog:
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    query_id: str = ""
    user_role: str = "sales"
    step: str = "retrieval_and_generation"
    input_query: str = ""
    processed_query: str = ""
    retrieval_results: list[dict[str, Any]] = field(default_factory=list)
    selected_context: list[str] = field(default_factory=list)
    final_prompt: str = ""
    final_answer: str = ""
    expected_document_id: list[str] = field(default_factory=list)
    expected_keywords: list[str] = field(default_factory=list)
    diagnosis: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class DebugSessionLogger:
    """Collects and organizes test case logs with correlation IDs."""

    def __init__(self, session_name: str = "default_session"):
        self.session_name = session_name
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now(UTC)
        self.logs: list[TestCaseLog] = []

    def create_case_log(
        self,
        query_id: str,
        input_query: str,
        user_role: str,
        expected_document_id: list[str] | str,
        expected_keywords: list[str] | None = None,
    ) -> TestCaseLog:
        exp_docs = (
            expected_document_id
            if isinstance(expected_document_id, list)
            else [expected_document_id]
        )
        case_log = TestCaseLog(
            query_id=query_id,
            input_query=input_query,
            user_role=user_role,
            expected_document_id=exp_docs,
            expected_keywords=expected_keywords or [],
        )
        self.logs.append(case_log)
        return case_log

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now(UTC).isoformat(),
            "total_cases": len(self.logs),
            "logs": [log.to_dict() for log in self.logs],
        }

    def save_json(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
