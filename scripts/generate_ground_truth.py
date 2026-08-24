"""
generate_ground_truth.py
Tự động sinh Ground Truth dataset từ chunk JSON files.
Sử dụng LLM (OpenAI) để tạo câu hỏi đại diện từ nội dung thực tế.
"""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("APP_ENV", "development")

from src.config import get_settings  # noqa: E402

settings = get_settings()

# ─── Candidate chunks lấy mẫu từ các tài liệu quan trọng ──────────────────────
SAMPLE_CONFIG = [
    # (file_pattern, role, max_samples)
    ("KeToan/01_huong_dan_dang_nhap_dms.json", "accounting", 3),
    ("KeToan/02_tao_khach_hang_tiem_nang.json", "accounting", 2),
    ("KeToan/03_quy_luat_kiem_tra_trung_khi_tao_lead.json", "accounting", 2),
    ("KeToan/10_them_chuong_trinh_khuyen_mai.json", "accounting", 2),
    ("KeToan/13_hop_dong_thue_pin.json", "accounting", 2),
    ("KeToan/20_dat_hang_ton_kho.json", "accounting", 2),
    ("KeToan/21_yeu_cau_hoan_coc_chuyen_coc_chuyen_san_pham.json", "accounting", 2),
    ("KeToan/22_huy_don_hang_new.json", "accounting", 2),
    ("KeToan/vf_hdsd_luong_claim_bu_ton_cho_xmd_v1_0.json", "accounting", 3),
    ("KeToan/vf_hdsd_thanh_ly_cham_dut_doi_chu_kich_hoat_lai_hdtp_dong_xe_doi_pin.json", "accounting", 2),
    ("Sale/4_tai_lieu_quy_trinh_va_ky_nang_ban_hang_xmd.json", "sales", 4),
    ("Sale/3_1_tieu_chuan_dich_vu_xmd_251121.json", "sales", 3),
    ("General_doc/260801_chinh_sach_ban_hang_xmd.json", "sales", 3),
    ("General_doc/2_lich_su_tong_quan_san_pham_xmd_260617.json", "sales", 2),
    ("KTV/1_chinh_sach_bao_hanh_xmd_ttvn.json", "technician", 3),
    ("KTV/2_dao_tao_vf_hm55_cho_xmd.json", "technician", 2),
    ("KTV/260727_vf_hmvn_dao_tao_bao_hanh_xdv_xmd_mo_moi.json", "technician", 3),
    ("KTV/vf_hdsd_huong_trinh_cham_soc_xe_mien_phi_danh_cho_vinfast_v1_0_7748.json", "technician", 2),
    ("General_doc/3_1_tieu_chuan_dich_vu_xmd_251121.json", "general", 2),
    ("General_doc/training_care.json", "general", 2),
]

CHUNKS_DIR = Path("Data/processed/chunks")


def load_samples() -> list[dict]:
    """Load random chunk samples theo config."""
    samples = []
    for rel_path, role, max_n in SAMPLE_CONFIG:
        fp = CHUNKS_DIR / rel_path
        if not fp.exists():
            print(f"  [SKIP] Not found: {fp}")
            continue
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            # Lọc chunk có content đủ dài (> 100 chars)
            valid = [c for c in data if len(c.get("content", "")) > 100]
            if not valid:
                continue
            selected = random.sample(valid, min(max_n, len(valid)))
            for chunk in selected:
                samples.append(
                    {
                        "chunk": chunk,
                        "role": role,
                        "source_file": rel_path,
                    }
                )
        except Exception as e:
            print(f"  [ERROR] {fp}: {e}")
    return samples


def extract_doc_id_prefix(chunk_id: str) -> str:
    """Trả về prefix trước _chunk_ để dùng làm expected_document_id."""
    if "_chunk_" in chunk_id:
        return "_".join(chunk_id.split("_chunk_")[0].split("_"))
    return chunk_id


def build_gt_entry(idx: int, chunk: dict, role: str) -> dict:
    """Tạo Ground Truth entry từ chunk metadata."""
    meta = chunk.get("metadata", {})
    doc_title = meta.get("document", "")
    section = meta.get("section", "")
    timestamp = meta.get("timestamp", "")
    chunk_id = chunk.get("chunk_id", "")

    # Lấy document_id prefix ngắn
    doc_prefix = chunk_id.split("_chunk_")[0] if "_chunk_" in chunk_id else chunk_id

    return {
        "query_id": f"GT{idx:03d}",
        "chunk_id_source": chunk_id,
        "role": role,
        "doc_title": doc_title,
        "section": section,
        "timestamp": timestamp or None,
        "expected_document_id": [doc_prefix],
        "raw_content_preview": chunk.get("raw_content", "")[:200].replace("\n", " "),
        # Câu hỏi và expected_answer sẽ được điền thủ công hoặc LLM
        "query": f"[GENERATED] {doc_title}: {section}",
        "expected_answer": "[TBD]",
        "query_type": "procedure",
        "expected_keywords": [],
    }


def main():
    random.seed(42)
    samples = load_samples()
    print(f"Loaded {len(samples)} chunk samples from {len(SAMPLE_CONFIG)} files")

    entries = []
    for i, s in enumerate(samples, start=1):
        entry = build_gt_entry(i, s["chunk"], s["role"])
        entries.append(entry)

    # Sắp xếp theo role
    entries.sort(key=lambda x: x["role"])

    out_path = Path("retrieval_debugger/ground_truth_candidates.json")
    out_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[OK] Saved {len(entries)} candidates -> {out_path}")
    print("   Tiếp theo: điền query + expected_answer bằng tay hoặc GPT")


if __name__ == "__main__":
    main()
