from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from src.preprocess.pii_remover import PIIRemover

logger = logging.getLogger(__name__)


@dataclass
class PIILocation:
    """Represents a single PII finding with precise location information."""

    entity_type: str  # e.g. "PHONE_NUMBER", "EMAIL_ADDRESS"
    masked_value: str  # Partially redacted value e.g. "0912***456"
    section_title: str  # Heading/section title where PII was found
    section_index: int  # Section index (0-based) in the document
    char_start: int  # Start character offset within section content
    char_end: int  # End character offset within section content
    context_before: str  # Up to 40 chars before the PII match
    context_after: str  # Up to 40 chars after the PII match
    confidence: float  # Detection confidence (0.0–1.0)
    requires_hitl: bool  # True if confidence < 0.75 (borderline detection)


@dataclass
class PIIScanResult:
    """Full PII scan results for a document."""

    has_pii: bool
    locations: list[PIILocation] = field(default_factory=list)
    cleaned_sections: dict[int, str] = field(default_factory=dict)  # section_idx -> cleaned text
    total_by_type: dict[str, int] = field(default_factory=dict)

    @property
    def hitl_required(self) -> bool:
        return any(loc.requires_hitl for loc in self.locations)

    @property
    def hitl_locations(self) -> list[PIILocation]:
        return [loc for loc in self.locations if loc.requires_hitl]

    @property
    def auto_removed_count(self) -> int:
        return sum(1 for loc in self.locations if not loc.requires_hitl)


# PII patterns with confidence levels for location tracking
# Each entry: (entity_type, regex_pattern, group_for_value, confidence, requires_hitl_threshold)
PII_LOCATION_PATTERNS: list[tuple[str, str, int | None, float]] = [
    ("EMAIL_ADDRESS", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", None, 0.95),
    ("PHONE_NUMBER", r"(?:\+84|84|0)(?:3[2-9]|5[25689]|7[06-9]|8[1-9]|9[0-9])\d{7}\b", None, 0.92),
    ("PHONE_NUMBER", r"\b0\d{9}\b", None, 0.75),
    ("CREDIT_CARD", r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b", None, 0.90),
    ("CUSTOMER_ID", r"\b(?:CUST|KH|CUSTOMER)[-_]?\d+\b", None, 0.88),
    ("EMPLOYEE_ID", r"\b(?:EMP|NV|EMPLOYEE)[-_]?\d+\b", None, 0.88),
    ("VEHICLE_PLATE", r"\b\d{2}[A-Z1-9][-\s]?\d{4,5}\b", None, 0.80),
    ("PASSWORD", r"(?:mật khẩu|password|pass|pwd):\s*(\S+)", 1, 0.92),
    ("USERNAME", r"(?:tên đăng nhập|tài khoản|username|user):\s*([A-Za-z0-9_.-]+)", 1, 0.90),
    ("BANK_ACCOUNT", r"(?:STK|số tài khoản|tài khoản ngân hàng):\s*(\d{8,16})", 1, 0.90),
    ("ID_NUMBER", r"(?:CCCD|CMND|số định danh|số ID):\s*(\d{9}|\d{12})", 1, 0.92),
]

HITL_CONFIDENCE_THRESHOLD = 0.78  # Below this, flag for human review


def _mask_value(value: str, entity_type: str) -> str:
    """Partially mask a PII value for safe display in reports."""
    if len(value) <= 4:
        return "***"
    if entity_type in ("PHONE_NUMBER",):
        return value[:4] + "***" + value[-3:]
    if entity_type in ("EMAIL_ADDRESS",):
        local, _, domain = value.partition("@")
        return local[:2] + "***@" + domain
    if entity_type in ("CREDIT_CARD", "BANK_ACCOUNT"):
        return "****" + value[-4:]
    if entity_type in ("ID_NUMBER",):
        return value[:3] + "***" + value[-2:]
    # Generic masking
    keep = max(2, len(value) // 4)
    return value[:keep] + "***" + value[-keep:]


class PIIScanner:
    """
    Enhanced PII scanner that:
    1. Detects PII in each document section independently
    2. Records precise location: section title, char_start, char_end, context
    3. Masks detected values for safe reporting
    4. Flags borderline detections (low-confidence) for HITL review
    5. Returns cleaned text per section
    """

    def __init__(self):
        self._remover = PIIRemover()

    def scan_sections(
        self,
        sections: list[dict],  # list of {"title": str, "content": str}
    ) -> PIIScanResult:
        """
        Scan a list of document sections for PII.

        Args:
            sections: List of dicts with 'title' and 'content' keys.

        Returns:
            PIIScanResult with locations, cleaned text, and HITL flags.
        """
        all_locations: list[PIILocation] = []
        cleaned_sections: dict[int, str] = {}
        total_by_type: dict[str, int] = {}

        for idx, section in enumerate(sections):
            title = section.get("title", f"Section {idx + 1}")
            content = section.get("content", "")

            if not content:
                cleaned_sections[idx] = content
                continue

            locations, cleaned_content = self._scan_text(content, title, idx)
            all_locations.extend(locations)
            cleaned_sections[idx] = cleaned_content

            for loc in locations:
                total_by_type[loc.entity_type] = total_by_type.get(loc.entity_type, 0) + 1

        has_pii = len(all_locations) > 0

        if has_pii:
            hitl_count = sum(1 for loc in all_locations if loc.requires_hitl)
            logger.info(f"PII scan complete: {len(all_locations)} findings ({hitl_count} require HITL review)")

        return PIIScanResult(
            has_pii=has_pii,
            locations=all_locations,
            cleaned_sections=cleaned_sections,
            total_by_type=total_by_type,
        )

    def scan_text(self, text: str, section_title: str = "Document") -> PIIScanResult:
        """Convenience method to scan a single text block."""
        sections = [{"title": section_title, "content": text}]
        return self.scan_sections(sections)

    def _scan_text(
        self,
        text: str,
        section_title: str,
        section_index: int,
    ) -> tuple[list[PIILocation], str]:
        """
        Scan a single text block, returning:
        - List of PIILocation findings
        - Cleaned text with PII replaced by placeholders
        """
        findings: list[tuple[int, int, str, float, str]] = []
        # (start, end, entity_type, confidence, raw_value)

        for entity_type, pattern, group_idx, confidence in PII_LOCATION_PATTERNS:
            flags = re.IGNORECASE if entity_type in ("CUSTOMER_ID", "EMPLOYEE_ID", "PASSWORD", "USERNAME") else 0

            for match in re.finditer(pattern, text, flags):
                if group_idx is not None:
                    try:
                        start, end = match.start(group_idx), match.end(group_idx)
                        raw_value = match.group(group_idx)
                    except IndexError:
                        start, end = match.start(), match.end()
                        raw_value = match.group(0)
                else:
                    start, end = match.start(), match.end()
                    raw_value = match.group(0)

                findings.append((start, end, entity_type, confidence, raw_value))

        if not findings:
            return [], text

        # Sort and deduplicate overlapping spans
        findings.sort(key=lambda x: (x[0], x[1]))
        merged: list[tuple[int, int, str, float, str]] = []
        for f in findings:
            if merged and f[0] < merged[-1][1]:
                # Overlapping — keep the one with higher confidence
                if f[3] > merged[-1][3]:
                    merged[-1] = f
            else:
                merged.append(f)

        # Build PIILocation objects
        locations: list[PIILocation] = []
        for start, end, entity_type, confidence, raw_value in merged:
            context_before = text[max(0, start - 40) : start]
            context_after = text[end : end + 40]
            masked = _mask_value(raw_value, entity_type)
            requires_hitl = confidence < HITL_CONFIDENCE_THRESHOLD

            locations.append(
                PIILocation(
                    entity_type=entity_type,
                    masked_value=masked,
                    section_title=section_title,
                    section_index=section_index,
                    char_start=start,
                    char_end=end,
                    context_before=context_before.replace("\n", " "),
                    context_after=context_after.replace("\n", " "),
                    confidence=confidence,
                    requires_hitl=requires_hitl,
                )
            )

        # Build cleaned text by replacing PII with [ENTITY_TYPE] placeholder
        cleaned_parts: list[str] = []
        last_idx = 0
        for start, end, entity_type, confidence, _ in merged:
            cleaned_parts.append(text[last_idx:start])
            cleaned_parts.append(f"[{entity_type}]")
            last_idx = end
        cleaned_parts.append(text[last_idx:])
        cleaned_text = "".join(cleaned_parts)
        cleaned_text = re.sub(r"[ \t]{2,}", " ", cleaned_text)

        return locations, cleaned_text
