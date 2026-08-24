r"""
CLI Test Tool for VF-Onboarding Copilot Ingestion Pipeline.

Usage:
    .\.venv\Scripts\python.exe scripts/test_input_pipeline.py <path_to_file> [--role manager] [--auto-approve]
"""

import argparse
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.file_validator import FileValidator
from src.ingestion.job_manager import JobStatus
from src.ingestion.pii_scanner import PIIScanner
from src.ingestion.security_scanner import SecurityScanner


def print_banner(text: str, char="="):
    print(f"\n{char * 60}")
    print(f"  {text}")
    print(f"{char * 60}")


def run_test(file_path: str, uploader: str = "manager", auto_approve: bool = False):
    p = Path(file_path)
    if not p.exists():
        print(f"[X] Error: File '{file_path}' does not exist.")
        return

    print_banner(f"TESTING INPUT INGESTION: {p.name}")
    print(f"[FILE] Path : {p.resolve()}")
    print(f"[SIZE] Size : {p.stat().st_size / 1024:.2f} KB")
    print(f"[USER] Uploaded By: {uploader}")

    # 1. File Validation
    print_banner("1. FILE VALIDATOR (Type, Size, Magic Bytes)", "-")
    validator = FileValidator()
    val_res = validator.validate(p)
    print(f"[OK] Valid Extension & Format : {val_res.is_valid}")
    if val_res.detected_mime:
        print(f"[OK] Detected MIME Type      : {val_res.detected_mime}")
    if val_res.errors:
        print(f"[ERR] Validation Errors       : {val_res.errors}")
    if val_res.warnings:
        print(f"[WARN] Validation Warnings     : {val_res.warnings}")

    if not val_res.is_valid:
        print("\n[REJECTED] File validation failed! Pipeline stopped.")
        return

    # 2. Extract Text Simulation / File Read
    print_banner("2. TEXT EXTRACTION / PREPROCESS PREVIEW", "-")
    try:
        if p.suffix.lower() in [".txt", ".md"]:
            text = p.read_text(encoding="utf-8", errors="ignore")
        else:
            text = f"Sample extracted text from {p.name} (Binary format)."
    except Exception as e:
        text = f"Extraction error: {e}"

    print(f"[TEXT] Extracted Length   : {len(text)} chars")
    print("[PREVIEW] First 250 chars:")
    clean_preview = text[:250].replace("\n", " ")
    print(f"   {clean_preview}...")

    # 3. Security Scan
    print_banner("3. SECURITY SCANNER (Macros, Viruses, Scripts, Executables)", "-")
    sec_scanner = SecurityScanner()
    sec_res = sec_scanner.scan_file(p, extracted_text=text)
    print(f"[SECURITY] Is Safe        : {sec_res.is_safe}")
    print(f"[SECURITY] Total Issues   : {len(sec_res.issues)}")
    if sec_res.issues:
        print(f"\n[ALERT] FOUND {len(sec_res.issues)} SECURITY ISSUES:")
        for idx, issue in enumerate(sec_res.issues, 1):
            print(f"   [{idx}] Type: {issue.issue_type} | Severity: {issue.severity}")
            print(f"       Detail: {issue.text_snippet}")
            if issue.location:
                print(f"       Location: {issue.location}")

    # 4. PII Scan
    print_banner("4. PII SCANNER (CCCD, SĐT, Email, VIN, Biển Số Xe, Thẻ Ngân Hàng)", "-")
    pii_scanner = PIIScanner()
    pii_res = pii_scanner.scan_text(text, section_title=p.name)
    print(f"[PII] Contains PII       : {pii_res.has_pii}")
    print(f"[PII] Total Found        : {len(pii_res.locations)}")

    if pii_res.locations:
        print("\n[PII LOCATIONS] (For HITL Review):")
        for idx, item in enumerate(pii_res.locations, 1):
            print(
                f"   [{idx}] Type: {item.entity_type} | Value: '{item.masked_value}' | Requires HITL: {item.requires_hitl}"
            )
            print(f"       Section: '{item.section_title}', Pos {item.char_start}-{item.char_end}")
            ctx = f"{item.context_before}[{item.masked_value}]{item.context_after}".replace("\n", " ")
            print(f'       Context: "...{ctx}..."')

    # 5. HITL Gate Decision
    print_banner("5. HITL (HUMAN-IN-THE-LOOP) GATE EVALUATION", "-")
    needs_hitl = (not sec_res.is_safe) or pii_res.has_pii
    if needs_hitl and not auto_approve:
        status = JobStatus.PENDING_REVIEW
        print("[STATUS] PENDING_REVIEW (Yêu cầu Manager duyệt thủ công)")
        reasons = []
        if not sec_res.is_safe:
            reasons.append(f"Security Issues ({len(sec_res.issues)})")
        if pii_res.has_pii:
            reasons.append(f"PII Detected ({len(pii_res.locations)})")
        print(f"  --> Lý do: {', '.join(reasons)}")
        print("  --> Manager UI Action: GET /api/v1/ingest/pending-review -> POST /api/v1/ingest/review/{job_id}")
    else:
        status = JobStatus.APPROVED if needs_hitl else JobStatus.CHUNKING
        print(f"[STATUS] {status.value} (Tự động đưa vào Chunking & Indexing vào ChromaDB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test VF Ingestion Input Pipeline")
    parser.add_argument("file_path", help="Path to input file to test")
    parser.add_argument("--role", default="manager", help="Role uploading (default: manager)")
    parser.add_argument("--auto-approve", action="store_true", help="Auto approve issues")
    args = parser.parse_args()

    run_test(args.file_path, args.role, args.auto_approve)
