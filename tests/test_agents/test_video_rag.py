from src.agents.nodes.rag_node import _build_doc_detail, _parse_timestamp_to_seconds


def test_parse_timestamp_to_seconds():
    # Valid mm:ss
    assert _parse_timestamp_to_seconds("01:47") == 107
    assert _parse_timestamp_to_seconds("00:30") == 30
    assert _parse_timestamp_to_seconds("00:00") == 0
    assert _parse_timestamp_to_seconds("10:05") == 605

    # Valid hh:mm:ss
    assert _parse_timestamp_to_seconds("01:05:30") == 3930

    # Non-timestamp or invalid
    assert _parse_timestamp_to_seconds("Overview") is None
    assert _parse_timestamp_to_seconds("") is None
    assert _parse_timestamp_to_seconds(None) is None
    assert _parse_timestamp_to_seconds("invalid:time:format:extra") is None


def test_build_doc_detail_document():
    chunk = {
        "metadata": {
            "document": "01_Huong_Dan_Ban_Hang.pdf",
            "section": "Chương 1",
            "source": "data/01_Huong_Dan_Ban_Hang.pdf",
            "content_type": "document",
        },
        "content": "[Context Header]\n\nNội dung hướng dẫn bán hàng xe máy điện VinFast...",
        "rerank_score": 4.5,
        "rrf_score": 0.85,
    }
    detail = _build_doc_detail(chunk)
    assert detail["doc_name"] == "01 Huong Dan Ban Hang"
    assert detail["section"] == "Chương 1"
    assert detail["rerank_score"] == 4.5
    assert detail["content_type"] == "document"
    assert detail["timestamp_seconds"] is None


def test_build_doc_detail_video():
    chunk = {
        "metadata": {
            "document": "Huong_Dan_Dang_Nhap_DMS.mp4",
            "section": "01:47",
            "source_path": "videos/Huong_Dan_Dang_Nhap_DMS.mp4",
            "content_type": "video",
        },
        "content": "Khi có thông báo tiếp tục ấn nút đăng nhập...",
        "rerank_score": 8.4,
        "rrf_score": 0.95,
    }
    detail = _build_doc_detail(chunk)
    assert detail["doc_name"] == "Huong Dan Dang Nhap Dms"
    assert detail["section"] == "01:47"
    assert detail["content_type"] == "video"
    assert detail["source_path"] == "videos/Huong_Dan_Dang_Nhap_DMS.mp4"
    assert detail["timestamp_seconds"] == 107
