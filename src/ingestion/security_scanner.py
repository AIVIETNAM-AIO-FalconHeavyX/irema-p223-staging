from __future__ import annotations

import logging
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SecurityIssue:
    """Represents a single security finding."""

    issue_type: str  # "MACRO_VBA", "PDF_JS", "PROMPT_INJECTION", "TOXIC_CONTENT", "ZIPBOMB"
    severity: str  # "HIGH", "MEDIUM", "LOW"
    location: str  # e.g. "page_3", "slide_7", "embedded_file: vbaProject.bin"
    text_snippet: str  # Up to 120 chars around the finding (redacted if malicious)
    confidence: float  # 0.0 – 1.0
    requires_hitl: bool  # True → human must review before proceeding
    auto_rejected: bool  # True → pipeline rejects without HITL (e.g. confirmed malware)


@dataclass
class SecurityScanResult:
    is_safe: bool
    issues: list[SecurityIssue] = field(default_factory=list)

    @property
    def has_auto_reject(self) -> bool:
        return any(i.auto_rejected for i in self.issues)

    @property
    def requires_hitl(self) -> bool:
        return any(i.requires_hitl for i in self.issues)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "HIGH")

    @property
    def medium_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "MEDIUM")


# ---------------------------------------------------------------------------
# Prompt injection patterns (conservative, low false-positive)
# ---------------------------------------------------------------------------

PROMPT_INJECTION_PATTERNS: list[tuple[str, str, float]] = [
    # (pattern, description, confidence)
    (
        r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
        "Classic prompt injection: ignore previous instructions",
        0.95,
    ),
    (
        r"(?i)you\s+are\s+now\s+(DAN|GPT|an?\s+AI\s+without\s+restrictions)",
        "Jailbreak: role override attempt",
        0.90,
    ),
    (
        r"(?i)<\|im_start\|>|<\|system\|>|\[SYSTEM\]|\[INST\]",
        "LLM instruction token injection",
        0.92,
    ),
    (
        r"(?i)disregard\s+(your\s+)?(previous|all|any)\s+(instructions?|guidelines?|rules?|constraints?)",
        "Prompt injection: disregard instructions",
        0.90,
    ),
    (
        r"(?i)(act\s+as|pretend\s+(you\s+are|to\s+be))\s+(an?\s+)?(?:AI|bot|assistant|model)\s+(?:without|that\s+ignores?)",
        "Jailbreak: pretend to be unrestricted AI",
        0.85,
    ),
    (
        r"(?si)---+\s*NEW\s+INSTRUCTIONS?\s*---+",
        "Instruction delimiter injection",
        0.88,
    ),
    (
        r"(?i)system\s+prompt\s*[:=]",
        "System prompt injection attempt",
        0.80,
    ),
    (
        r"(?i)(leak|reveal|print|show|output)\s+(your\s+)?(system\s+prompt|instructions?|context|configuration)",
        "Prompt extraction attempt",
        0.85,
    ),
]

# ---------------------------------------------------------------------------
# Basic toxic/NSFW keywords (Vietnamese + English — minimal wordlist for MVP)
# ---------------------------------------------------------------------------
# This is a conservative list targeting clearly harmful content.
# Expand with a proper moderation service in production.
TOXIC_PATTERNS: list[tuple[str, str]] = [
    (
        r"(?i)\b(bom|bomb|explosive|thuốc\s+nổ)\b.{0,50}\b(how\s+to|cách\s+làm|hướng\s+dẫn)",
        "Bomb/explosive instructions",
    ),
    (
        r"(?i)\b(synthesis|tổng\s+hợp|chế\s+tạo)\b.{0,50}\b(drug|ma\s+túy|heroin|methamphetamine|fentanyl)",
        "Drug synthesis",
    ),
    (r"(?i)\b(hack|phishing|malware|ransomware)\b.{0,50}\b(script|code|payload|inject)", "Malicious code instruction"),
]


# ---------------------------------------------------------------------------
# PDF dangerous action patterns (inside raw PDF bytes)
# ---------------------------------------------------------------------------
PDF_DANGEROUS_PATTERNS: list[tuple[bytes, str]] = [
    (b"/JS", "PDF JavaScript action"),
    (b"/JavaScript", "PDF JavaScript dictionary"),
    (b"/Launch", "PDF Launch action (can execute external programs)"),
    (b"/OpenAction", "PDF OpenAction (auto-executes on open)"),
    (b"/AA", "PDF Additional Actions"),
    (b"/URI", "PDF URI action"),
    (b"/SubmitForm", "PDF form auto-submission"),
    (b"/ImportData", "PDF data import action"),
    (b"/RichMedia", "PDF RichMedia (Flash/video embed)"),
]


class SecurityScanner:
    """
    Scans documents for security threats:
    1. Office macro / VBA detection (DOCX, XLSX, PPTX)
    2. PDF dangerous actions (JavaScript, Launch, AutoOpen)
    3. Prompt injection / jailbreak patterns in text content
    4. Basic toxic content patterns
    """

    def scan_file(self, file_path: Path, extracted_text: str = "") -> SecurityScanResult:
        """
        Run all security checks on a file.

        Args:
            file_path: Path to the original uploaded file.
            extracted_text: Full plain text extracted from the document (for text-based checks).

        Returns:
            SecurityScanResult with a list of SecurityIssue findings.
        """
        issues: list[SecurityIssue] = []
        ext = file_path.suffix.lower()

        # --- File-based checks ---
        if ext in (".docx", ".pptx", ".xlsx"):
            issues.extend(self._scan_office_macros(file_path))
        elif ext == ".pdf":
            issues.extend(self._scan_pdf_actions(file_path))

        # --- Text-based checks ---
        if extracted_text:
            issues.extend(self._scan_prompt_injection(extracted_text))
            issues.extend(self._scan_toxic_content(extracted_text))

        is_safe = not any(i.auto_rejected for i in issues) and len([i for i in issues if i.severity == "HIGH"]) == 0

        result = SecurityScanResult(is_safe=is_safe, issues=issues)

        if issues:
            logger.warning(
                f"Security scan found {len(issues)} issue(s) in {file_path.name}: "
                f"HIGH={result.high_count}, MEDIUM={result.medium_count}"
            )
        else:
            logger.info(f"Security scan passed: {file_path.name}")

        return result

    # ------------------------------------------------------------------
    # Office macro detection
    # ------------------------------------------------------------------

    def _scan_office_macros(self, file_path: Path) -> list[SecurityIssue]:
        """Detect VBA macros inside DOCX/XLSX/PPTX (ZIP containers)."""
        issues: list[SecurityIssue] = []
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                names = zf.namelist()

                # vbaProject.bin = compiled VBA macro storage
                vba_files = [n for n in names if "vbaProject" in n or n.endswith(".bin")]
                if vba_files:
                    for vba_file in vba_files:
                        issues.append(
                            SecurityIssue(
                                issue_type="MACRO_VBA",
                                severity="HIGH",
                                location=f"embedded_file: {vba_file}",
                                text_snippet=(
                                    "VBA macro storage detected. Macros can execute "
                                    "arbitrary code when the document is opened."
                                ),
                                confidence=0.98,
                                requires_hitl=True,
                                auto_rejected=False,  # Require human decision — legitimate docs sometimes have macros
                            )
                        )

                # Check for XML-level macro references
                for name in names:
                    if name.endswith(".xml") or name.endswith(".rels"):
                        try:
                            content = zf.read(name).decode("utf-8", errors="ignore")
                            if "macroEnabled" in content or "vbaData" in content:
                                if not any(i.issue_type == "MACRO_VBA" for i in issues):
                                    issues.append(
                                        SecurityIssue(
                                            issue_type="MACRO_VBA",
                                            severity="HIGH",
                                            location=f"xml_reference: {name}",
                                            text_snippet="Macro-enabled reference found in document XML.",
                                            confidence=0.85,
                                            requires_hitl=True,
                                            auto_rejected=False,
                                        )
                                    )
                                    break
                        except Exception:
                            pass

        except zipfile.BadZipFile:
            pass
        except Exception as e:
            logger.debug(f"Office macro scan error for {file_path}: {e}")

        return issues

    # ------------------------------------------------------------------
    # PDF dangerous action detection
    # ------------------------------------------------------------------

    def _scan_pdf_actions(self, file_path: Path) -> list[SecurityIssue]:
        """Scan raw PDF bytes for dangerous action keywords."""
        issues: list[SecurityIssue] = []
        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large PDFs without loading all into RAM
                content = b""
                for _ in range(20):  # max 20 * 64KB = 1.28 MB of PDF header/xref
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    content += chunk

            for pattern_bytes, description in PDF_DANGEROUS_PATTERNS:
                if pattern_bytes in content:
                    # Find context around the pattern
                    idx = content.find(pattern_bytes)
                    snippet_raw = content[max(0, idx - 20) : idx + 60]
                    snippet = snippet_raw.decode("latin-1", errors="replace").strip()

                    # /URI is less dangerous than /JS — rate accordingly
                    if pattern_bytes in (b"/URI", b"/RichMedia"):
                        severity, confidence, auto_rejected = "LOW", 0.60, False
                        requires_hitl = False
                    elif pattern_bytes in (b"/OpenAction", b"/AA"):
                        severity, confidence, auto_rejected = "MEDIUM", 0.80, False
                        requires_hitl = True
                    else:
                        severity, confidence, auto_rejected = "HIGH", 0.90, False
                        requires_hitl = True

                    issues.append(
                        SecurityIssue(
                            issue_type="PDF_DANGEROUS_ACTION",
                            severity=severity,
                            location=f"pdf_byte_offset: {idx}",
                            text_snippet=f"{description}: ...{snippet}...",
                            confidence=confidence,
                            requires_hitl=requires_hitl,
                            auto_rejected=auto_rejected,
                        )
                    )

        except Exception as e:
            logger.debug(f"PDF action scan error for {file_path}: {e}")

        return issues

    # ------------------------------------------------------------------
    # Prompt injection detection
    # ------------------------------------------------------------------

    def _scan_prompt_injection(self, text: str) -> list[SecurityIssue]:
        """Detect prompt injection / jailbreak patterns in extracted text."""
        issues: list[SecurityIssue] = []

        for pattern, description, confidence in PROMPT_INJECTION_PATTERNS:
            for match in re.finditer(pattern, text):
                start = match.start()
                snippet = text[max(0, start - 30) : start + 100].replace("\n", " ").strip()

                # Find approximate location (paragraph number)
                paragraph_num = text[:start].count("\n\n") + 1

                issues.append(
                    SecurityIssue(
                        issue_type="PROMPT_INJECTION",
                        severity="MEDIUM",
                        location=f"paragraph_{paragraph_num}",
                        text_snippet=f"...{snippet}...",
                        confidence=confidence,
                        requires_hitl=True,
                        auto_rejected=False,
                    )
                )

        return issues

    # ------------------------------------------------------------------
    # Toxic content detection
    # ------------------------------------------------------------------

    def _scan_toxic_content(self, text: str) -> list[SecurityIssue]:
        """Basic toxic/harmful content pattern matching."""
        issues: list[SecurityIssue] = []

        for pattern, description in TOXIC_PATTERNS:
            for match in re.finditer(pattern, text):
                start = match.start()
                snippet = text[max(0, start - 20) : start + 80].replace("\n", " ").strip()
                paragraph_num = text[:start].count("\n\n") + 1

                issues.append(
                    SecurityIssue(
                        issue_type="TOXIC_CONTENT",
                        severity="HIGH",
                        location=f"paragraph_{paragraph_num}",
                        text_snippet=f"...{snippet}...",
                        confidence=0.85,
                        requires_hitl=True,
                        auto_rejected=True,  # Auto-reject confirmed harmful instructions
                    )
                )

        return issues
