#!/usr/bin/env python3
"""
run_preprocessing.py - CLI for the RAG Data Preprocessing & Ingestion Pipeline.

Modes:
  Default       : Extract -> PII removal -> Markdown -> (no security scan)
  --scan-only   : Validate + Security scan + PII scan only. Print report. Do NOT index.
  --auto-approve: Run full pipeline without stopping for HITL review (e.g. for CI/CD).
  --gemini-ocr  : Force Gemini Vision OCR for all pages (even if PyMuPDF extracts text).

Examples:
  # Process all files in data/raw:
  python scripts/run_preprocessing.py

  # Process single file:
  python scripts/run_preprocessing.py --file "data/raw/General_doc/report.pdf"

  # Scan-only (no indexing):
  python scripts/run_preprocessing.py --file "data/raw/contract.pdf" --scan-only

  # Full pipeline, skip HITL:
  python scripts/run_preprocessing.py --file "data/raw/doc.pdf" --auto-approve
"""

from __future__ import annotations

import os

# Disable PyTorch inductor C++ compiler lookup (cl.exe on Windows)
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["PYTORCH_JIT"] = "0"
os.environ["OMP_NUM_THREADS"] = "1"

import argparse
import json
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.file_validator import FileValidator
from src.ingestion.pii_scanner import PIIScanner
from src.ingestion.security_scanner import SecurityScanner
from src.preprocess.pipeline import PreprocessingPipeline

# ANSI colour helpers (safe fallback for Windows without colorama)
try:
    import colorama

    colorama.init(autoreset=True)
    RED = colorama.Fore.RED
    YELLOW = colorama.Fore.YELLOW
    GREEN = colorama.Fore.GREEN
    CYAN = colorama.Fore.CYAN
    RESET = colorama.Style.RESET_ALL
except ImportError:
    RED = YELLOW = GREEN = CYAN = RESET = ""


def _print_separator(char: str = "-", width: int = 70) -> None:
    print(char * width)


def _print_scan_report(
    file_path: Path,
    validator: FileValidator,
    sec_scanner: SecurityScanner,
    pii_scanner: PIIScanner,
    extracted_text: str,
    sections: list[dict],
) -> bool:
    """
    Print a human-friendly security + PII scan report.
    Returns True if the file is safe to proceed, False if there are blocking issues.
    """
    _print_separator("=")
    print(f"SCAN REPORT: {file_path.name}")
    _print_separator("=")

    # --- 1. File Validation ---
    print("\n[1] FILE VALIDATION")
    validation = validator.validate(file_path)
    if validation.is_valid:
        print(f"  OK  Valid ({validation.file_size_bytes / 1024:.1f} KB, type={validation.detected_mime})")
    else:
        print("  INVALID")
        for err in validation.errors:
            print(f"     - {err}")
        return False
    for w in validation.warnings:
        print(f"  WARNING: {w}")

    # --- 2. Security Scan ---
    print("\n[2] SECURITY SCAN")
    sec_result = sec_scanner.scan_file(file_path, extracted_text=extracted_text)
    if not sec_result.issues:
        print("  OK  No security issues found.")
    else:
        for issue in sec_result.issues:
            hitl_tag = " [HITL-REVIEW]" if issue.requires_hitl else ""
            reject_tag = " [AUTO-REJECTED]" if issue.auto_rejected else ""
            print(f"  [{issue.severity}] {issue.issue_type}{hitl_tag}{reject_tag}")
            print(f"     Location   : {issue.location}")
            print(f"     Snippet    : {issue.text_snippet[:100]}")
            print(f"     Confidence : {issue.confidence:.0%}")

    # --- 3. PII Scan ---
    print("\n[3] PII SCAN")
    pii_result = pii_scanner.scan_sections(sections)
    if not pii_result.has_pii:
        print("  OK  No PII detected.")
    else:
        auto_removed = [loc for loc in pii_result.locations if not loc.requires_hitl]
        hitl_needed = pii_result.hitl_locations

        if auto_removed:
            print(f"  OK  {len(auto_removed)} PII item(s) auto-removed (high confidence):")
            for loc in auto_removed[:5]:
                print(
                    f'     - [{loc.entity_type}] {loc.masked_value!r}  in "{loc.section_title}" '
                    f"(char {loc.char_start}-{loc.char_end})"
                )
            if len(auto_removed) > 5:
                print(f"     ... and {len(auto_removed) - 5} more.")

        if hitl_needed:
            print(f"\n  WARNING: {len(hitl_needed)} PII item(s) require HUMAN REVIEW (low confidence):")
            for i, loc in enumerate(hitl_needed):
                print(f"\n  [{i + 1}] [{loc.entity_type}] masked={loc.masked_value!r}")
                print(f'      Section    : "{loc.section_title}" (index {loc.section_index})')
                print(f"      Context    : ...{loc.context_before}|MATCH|{loc.context_after}...")
                print(f"      Confidence : {loc.confidence:.0%}  <- Below threshold, please verify")

    # --- Summary ---
    _print_separator()
    has_auto_reject = sec_result.has_auto_reject
    has_high = sec_result.high_count > 0
    needs_hitl = sec_result.requires_hitl or pii_result.hitl_required

    if has_auto_reject:
        print("\nRESULT: AUTO-REJECTED - Document contains confirmed malicious content.")
        return False
    elif has_high:
        print("\nRESULT: HIGH severity issues found. HITL review required before indexing.")
    elif needs_hitl:
        print("\nRESULT: Medium/low-confidence issues found. HITL review recommended.")
    else:
        print("\nRESULT: File is safe to index.")
    _print_separator("=")
    return not has_auto_reject


def _extract_for_scan(
    file_path: Path,
    pipeline: PreprocessingPipeline,
) -> tuple[str, list[dict]]:
    """Lightly extract text for security scanning without full pipeline run."""
    ext = file_path.suffix.lower()
    extractor = pipeline.extractors.get(ext)
    if not extractor:
        return "", []
    try:
        role, category, _ = pipeline.detect_role_and_scope(file_path)
        doc = extractor.extract(file_path, role=role, category=category)
        extracted_text = doc.raw_text or ""
        sections = [
            {"title": s.title or f"Section {i}", "content": s.content} for i, s in enumerate(doc.sections) if s.content
        ]
        return extracted_text, sections
    except Exception as e:
        logging.warning(f"Could not extract text for scan (file bytes scan only): {e}")
        return "", []


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="RAG Data Preprocessing & Ingestion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default="Data/raw",
        help="Input raw documents directory (default: data/raw)",
    )
    parser.add_argument(
        "--processed-dir",
        type=str,
        default="Data/processed",
        help="Output processed directory (default: data/processed)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Optional specific single file path to process",
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        default=False,
        help=(
            "Run file validation + security scan + PII scan only. "
            "Print a detailed report. Do NOT run extraction or indexing."
        ),
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        default=False,
        help=(
            "Automatically approve all HITL flags and proceed with indexing. "
            "Use for CI/CD pipelines where human review is done separately."
        ),
    )
    parser.add_argument(
        "--gemini-ocr",
        action="store_true",
        default=False,
        help=(
            "Force Gemini Vision API for OCR on all pages (requires GOOGLE_API_KEY). "
            "Best for PDF slides with complex layouts."
        ),
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.gemini_ocr:
        print("INFO: --gemini-ocr flag set. Gemini Vision API will be preferred for OCR pages.")

    pipeline = PreprocessingPipeline(
        raw_dir=args.raw_dir,
        processed_dir=args.processed_dir,
    )

    validator = FileValidator()
    sec_scanner = SecurityScanner()
    pii_scanner = PIIScanner()

    # -------------------------------------------------------------------
    # Single file mode
    # -------------------------------------------------------------------
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        # ---- Scan-only mode ----
        if args.scan_only:
            print("\nMode: SCAN ONLY (no extraction or indexing)\n")
            extracted_text, sections = _extract_for_scan(file_path, pipeline)
            is_safe = _print_scan_report(file_path, validator, sec_scanner, pii_scanner, extracted_text, sections)
            sys.exit(0 if is_safe else 1)

        # ---- Full pipeline mode ----
        print(f"\nProcessing: {file_path.name}")
        if args.auto_approve:
            print("INFO: --auto-approve: All HITL flags will be bypassed.")

        res = pipeline.process_file(file_path)
        if res:
            md_path, meta_path, pii_path = res
            print("\nSuccessfully processed:")
            print(f"  Markdown   : {md_path}")
            print(f"  Metadata   : {meta_path}")
            print(f"  PII Report : {pii_path}")

            # Print brief PII summary
            try:
                pii_data = json.loads(pii_path.read_text(encoding="utf-8"))
                if pii_data.get("detected"):
                    counts = pii_data.get("removed_counts", {})
                    print(f"  PII removed: {dict(counts)}")
            except Exception:
                pass
        else:
            print(f"Failed or skipped: {file_path}")
            sys.exit(1)

    # -------------------------------------------------------------------
    # Batch mode
    # -------------------------------------------------------------------
    else:
        if args.scan_only:
            print(f"\nMode: BATCH SCAN ONLY - scanning all files in {pipeline.raw_dir}\n")
            all_safe = True
            for file_path in sorted(pipeline.raw_dir.rglob("*")):
                if file_path.is_file() and file_path.suffix.lower() in pipeline.extractors:
                    extracted_text, sections_ = _extract_for_scan(file_path, pipeline)
                    is_safe = _print_scan_report(
                        file_path, validator, sec_scanner, pii_scanner, extracted_text, sections_
                    )
                    if not is_safe:
                        all_safe = False
            sys.exit(0 if all_safe else 1)

        print(f"\nScanning directory recursively: {pipeline.raw_dir} ...")
        results = pipeline.run_all()
        print(f"\nProcessing Complete! Total files processed: {len(results)}")
        for md_path, meta_path, pii_path in results:
            print(f"  OK  {md_path.name}")


if __name__ == "__main__":
    main()
