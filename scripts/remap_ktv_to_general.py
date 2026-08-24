"""
scripts/remap_ktv_to_general.py
Chuyển 3 file KTV phù hợp cho Sales sang role=general + access_scope=all roles.
Sau khi chạy: python scripts/rebuild_vector_db.py để rebuild ChromaDB.
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

CHUNKS_DIR = Path("Data/processed/chunks/KTV")

# 3 file cho Sale/General xem -- không chứa thông tin nội bộ KTV nhạy cảm
TARGET_FILES = [
    "1_chinh_sach_bao_hanh_xmd_ttvn.json",
    "2_dao_tao_vf_hm55_cho_xmd.json",
    "vf_hdsd_huong_trinh_cham_soc_xe_mien_phi_danh_cho_vinfast_v1_0_7748.json",
]

ALL_ROLES = ["accounting", "sales", "technician", "owner", "general"]


def remap(file_path: Path) -> int:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    changed = 0
    for chunk in data:
        meta = chunk.get("metadata", {})
        old_role = meta.get("role", "?")
        old_scope = meta.get("access_scope", [])

        # Chỉ update nếu cần
        if meta.get("role") != "general" or set(meta.get("access_scope", [])) != set(ALL_ROLES):
            meta["role"] = "general"
            meta["access_scope"] = ALL_ROLES
            chunk["metadata"] = meta
            changed += 1

        # Cập nhật content header (CCH prefix)
        content = chunk.get("content", "")
        if f"Role: {old_role}" in content:
            chunk["content"] = content.replace(f"Role: {old_role}", "Role: general", 1)

    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


def main():
    print("Remapping KTV -> general for 3 shared knowledge files...")
    total = 0
    for fname in TARGET_FILES:
        fp = CHUNKS_DIR / fname
        if not fp.exists():
            print(f"  [SKIP] Not found: {fp}")
            continue
        n = remap(fp)
        total += n
        print(f"  [OK] {fname}: {n} chunks updated -> role=general, access_scope=all")

    print(f"\nDone. {total} chunks remapped.")
    print("Tiep theo: python scripts/rebuild_vector_db.py")


if __name__ == "__main__":
    main()
