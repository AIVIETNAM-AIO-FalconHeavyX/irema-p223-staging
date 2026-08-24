"""Kiểm tra mọi tài liệu tham chiếu trong catalog onboarding có thật trên đĩa.

Chạy:  python -m scripts.verify_onboarding_resources
Thoát code 1 nếu có đường dẫn sai — dùng được trong CI.
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.content.onboarding_catalog import ROLE_ONBOARDING_CATALOG
from src.media import media_root


def main() -> int:
    root: Path = media_root()
    missing: list[tuple[str, str, str]] = []
    total = 0

    for role, steps in ROLE_ONBOARDING_CATALOG.items():
        for step in steps:
            for res in step["resources"]:
                total += 1
                if not (root / res["path"]).is_file():
                    missing.append((role, step["title"], res["path"]))

    print(f"Thư mục gốc : {root}")
    print(f"Đã kiểm tra : {total} tài liệu trong {len(ROLE_ONBOARDING_CATALOG)} vai trò")

    if missing:
        print(f"\n❌ Thiếu {len(missing)} file:")
        for role, title, path in missing:
            print(f"  [{role}] {title}\n      -> {path}")
        return 1

    print("\n✅ Tất cả tài liệu đều tồn tại.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
