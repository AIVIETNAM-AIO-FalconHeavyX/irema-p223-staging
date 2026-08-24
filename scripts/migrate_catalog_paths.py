#!/usr/bin/env python3
import re
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import unicodedata


def build_real_paths_map():
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        return {}

    mapping = {}
    for f in raw_dir.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            nfc_name = unicodedata.normalize("NFC", f.name)
            mapping[nfc_name] = str(f.relative_to(raw_dir))
    return mapping


def run_migration():
    catalog_path = Path("src/content/onboarding_catalog.py")
    with open(catalog_path, encoding="utf-8") as f:
        lines = f.readlines()

    real_paths = build_real_paths_map()

    # Update CATALOG_VERSION
    for i, line in enumerate(lines):
        if line.startswith("CATALOG_VERSION ="):
            lines[i] = 'CATALOG_VERSION = "2026.08.20-minio-v2"\n'
            break

    content = "".join(lines)

    import ast

    def replacer(match):
        full_match = match.group(0)
        try:
            string_part = (
                full_match.split("path':", 1)[1] if "path':" in full_match else full_match.split('path":', 1)[1]
            )
            if string_part.endswith(","):
                string_part = string_part[:-1]
            val = ast.literal_eval(string_part.strip())

            filename = val.split("/")[-1]
            nfc_filename = unicodedata.normalize("NFC", filename)
            if nfc_filename in real_paths:
                new_path = f"s3://{real_paths[nfc_filename]}"
                prefix = full_match.split("path")[0] + "path"
                if "path':" in full_match:
                    return f"{prefix}': '{new_path}'"
                else:
                    return f'{prefix}": "{new_path}"'
            else:
                return full_match
        except Exception:
            return full_match

    pattern = re.compile(r"('path'|\"path\"):\s*(?:'[^']*'|\"[^\"]*\")(?:\s*(?:'[^']*'|\"[^\"]*\"))*")
    new_content = pattern.sub(replacer, content)

    with open(catalog_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("Migration successful! Wrote new paths to onboarding_catalog.py")


if __name__ == "__main__":
    run_migration()
