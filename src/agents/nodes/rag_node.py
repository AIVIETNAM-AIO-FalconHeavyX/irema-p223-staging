import logging
import re

from src.agents.state import AgentState
from src.config import get_settings
from src.services.llm import get_llm
from src.vectordb.hybrid_search import HybridRetriever
from src.vectordb.postgres_hybrid_search import PostgresHybridRetriever
from src.vectordb.reranker import RerankerService

logger = logging.getLogger(__name__)

# Singletons for vector store / hybrid retriever / reranker
_retriever: HybridRetriever | PostgresHybridRetriever | None = None
_reranker: RerankerService | None = None
_rag_models_ready = False


def is_rag_ready() -> bool:
    """Kiểm tra retriever và Cohere reranker đã sẵn sàng phục vụ hay chưa."""
    return _rag_models_ready


def set_rag_ready(status: bool) -> None:
    """Cập nhật trạng thái sẵn sàng của mô hình RAG."""
    global _rag_models_ready
    _rag_models_ready = status


def get_retriever() -> HybridRetriever | PostgresHybridRetriever:
    global _retriever
    if _retriever is None:
        settings = get_settings()
        _retriever = PostgresHybridRetriever() if settings.retrieval_backend == "postgres" else HybridRetriever()
    return _retriever


def get_reranker() -> RerankerService:
    global _reranker
    if _reranker is None:
        _reranker = RerankerService()
    return _reranker


def init_rag_models() -> tuple[HybridRetriever | PostgresHybridRetriever, RerankerService]:
    """
    Khởi tạo retriever (SentenceTransformer, ChromaDB, BM25) và Cohere reranker
    ngay khi backend (FastAPI) khởi động.
    """
    global _rag_models_ready
    logger.info("Initializing and pre-loading RAG models on backend startup...")
    retriever = get_retriever()
    reranker = get_reranker()

    # Pre-warm models with dummy query to trigger lazy load into memory
    try:
        retriever.search(query_text="warmup", top_k=1, role="general", access_scope=["general"])
        reranker.rerank(query_text="warmup", candidates=[])
        _rag_models_ready = True
        logger.info("RAG models pre-loaded and warmed up successfully.")
    except Exception as e:
        logger.warning(f"RAG model warm-up warning: {e}")
        _rag_models_ready = True

    return retriever, reranker


def _parse_timestamp_to_seconds(ts: str) -> int | None:
    """
    Convert timestamp string 'MM:SS' hoặc 'HH:MM:SS' sang số giây.
    Trả về None nếu không phải timestamp hợp lệ.

    Examples:
        '01:47' → 107
        '00:30' → 30
        '01:05:30' → 3930
        'Overview' → None
    """
    if not ts:
        return None
    parts = ts.strip().split(":")
    try:
        if len(parts) == 2:  # noqa: PLR2004
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3:  # noqa: PLR2004
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, IndexError):
        pass
    return None


def _build_doc_detail(chunk: dict) -> dict:
    """
    Xây dựng dict metadata chi tiết cho một chunk đã rerank.
    Dùng để hiển thị source badges và video player trong frontend.

    Returns dict:
        doc_name: Tên tài liệu (clean, không extension)
        section: Tên mục/section
        rerank_score: Cohere relevance score trong khoảng [0, 1]
        rrf_score: Score từ Hybrid RRF
        content_preview: 150 ký tự đầu của nội dung chunk
        content_type: 'video' | 'document'
        source_path: Đường dẫn file gốc (để build video URL)
        timestamp_seconds: Giây trong video (None nếu không phải video)
    """
    meta = chunk.get("metadata", {})

    # Clean tên tài liệu
    raw_doc_name = (
        meta.get("document") or meta.get("title") or meta.get("document_id") or meta.get("source") or "Tài liệu VinFast"
    )
    doc_name = str(raw_doc_name)
    if "/" in doc_name or "\\" in doc_name:
        doc_name = doc_name.replace("\\", "/").split("/")[-1]
    for ext in [".pdf", ".docx", ".xlsx", ".pptx", ".md", ".txt", ".csv", ".mp4", ".mov", ".avi"]:
        if doc_name.lower().endswith(ext):
            doc_name = doc_name[: -len(ext)]
            break
    if "_" in doc_name and " " not in doc_name:
        doc_name = doc_name.replace("_", " ").title()

    section = meta.get("section") or meta.get("subsection") or ""
    rerank_score = chunk.get("rerank_score", chunk.get("rrf_score", 0.0))
    rrf_score = chunk.get("rrf_score", 0.0)

    # Content preview (150 chars, strip context header)
    raw_content = chunk.get("raw_content") or chunk.get("content", "")
    content_clean = re.sub(r"^\[.*?\]\n\n", "", raw_content, flags=re.DOTALL).strip()
    content_preview = content_clean[:150].strip()
    if len(content_clean) > 150:
        content_preview += "..."

    # -------------------------------------------------------
    # Video metadata
    # -------------------------------------------------------
    # content_type: lấy từ metadata (video_extractor set 'video') hoặc suy ra từ extension
    chunk_content_type = meta.get("content_type", "document")
    source_path_raw = meta.get("source_path") or meta.get("source") or ""
    # Normalize source_path: bỏ prefix, chỉ giữ relative path
    source_path = str(source_path_raw).replace("\\", "/")

    # Nếu source_path chứa .mp4/.mov → gán content_type = video
    video_exts = (".mp4", ".mov", ".avi", ".mkv", ".webm")
    if any(source_path.lower().endswith(e) for e in video_exts):
        chunk_content_type = "video"

    # Parse timestamp từ section (ví dụ: '01:47' → 107)
    timestamp_seconds: int | None = None
    if chunk_content_type == "video" and section:
        timestamp_seconds = _parse_timestamp_to_seconds(section)

    return {
        "doc_name": doc_name,
        "section": section,
        "rerank_score": float(rerank_score or 0.0),
        "rrf_score": float(rrf_score or 0.0),
        "content_preview": content_preview,
        "content_type": chunk_content_type,
        "source_path": source_path,
        "timestamp_seconds": timestamp_seconds,
    }


async def rag_node(state: AgentState) -> dict:
    """
    Tra cứu tài liệu RAG sử dụng Hybrid Search (ChromaDB + BM25Okapi),
    Cross-Encoder Reranking và Phân quyền RBAC theo vai trò người dùng.

    Improvements:
    - Fetch 40 candidates thay vì 25 (rộng hơn để reranker lọc tốt hơn).
    - Rerank còn top 5 (thay vì 8) với min_score_threshold.
    - Build retrieved_docs_detail cho frontend source badges.
    """
    raw_role = str(state.get("user_role") or "").lower()
    role_norm = {
        "accountant": "accounting",
        "ketoan": "accounting",
        "accounting": "accounting",
        "sale": "sales",
        "sales": "sales",
        "ktv": "technician",
        "technician": "technician",
        "manager": "owner",
        "owner": "owner",
        "admin": "owner",
    }
    user_role = role_norm.get(raw_role, raw_role)

    raw_query = state.get("raw_query") or state.get("query") or ""
    rewritten_query = state.get("rewritten_query") or raw_query

    # Bỏ tiền tố vai trò [SALES] nếu có để search chuẩn xác
    search_query = re.sub(r"^\[[A-Z_]+\]\s*", "", rewritten_query).strip() or raw_query

    settings = get_settings()

    if user_role in ("owner", "manager"):
        access_scope = ["accounting", "sales", "technician", "general", "owner", "manager"]
    else:
        access_scope = list(settings.access_scope_mapping.get(user_role, [user_role, "general"]))
        if "general" not in access_scope:
            access_scope.append("general")

    retriever = get_retriever()
    reranker = get_reranker()

    # 1. Hybrid Search: fetch 40 candidates (tăng từ 25 để reranker có nhiều lựa chọn hơn)
    candidates = retriever.search(
        query_text=search_query,
        retrieval_queries=state.get("retrieval_queries") or [search_query],
        top_k=40,
        role=user_role,
        access_scope=access_scope,
    )

    # 2. Cross-Encoder Reranking: top 5 với min_score_threshold từ config
    top_chunks = reranker.rerank(query_text=raw_query, candidates=candidates, top_k=5)

    existing_context = state.get("context", "")
    existing_citations = state.get("citations", [])

    if not top_chunks:
        if existing_context:
            context_text = existing_context
            citations = existing_citations
            rag_confidence = state.get("rag_confidence", 0.7)
            needs_escalation = False
        else:
            context_text = "Không tìm thấy thông tin phù hợp trong tài liệu được cấp quyền."
            citations = []
            rag_confidence = 0.2
            needs_escalation = True

        return {
            "context": context_text,
            "retrieved_docs": [],
            "retrieved_docs_detail": [],
            "citations": citations,
            "rag_confidence": rag_confidence,
            "needs_escalation": needs_escalation,
        }

    # 3. Build Prompt Context & Citations Mapping
    context_parts = []
    doc_map: dict[int, list[str]] = {}

    if existing_context:
        context_parts.append(f"[TÀI LIỆU 0: Ngữ cảnh từ quy trình / sự cố trước đó]\n{existing_context}")
        if existing_citations:
            doc_map[0] = list(existing_citations)

    for i, chunk in enumerate(top_chunks, start=1):
        meta = chunk.get("metadata", {})
        role_label = meta.get("role", "general")
        section = meta.get("section", "N/A")

        # Clean human-readable document title
        raw_doc_name = (
            meta.get("document")
            or meta.get("title")
            or meta.get("document_id")
            or meta.get("source")
            or "Tài liệu VinFast"
        )
        doc_name = str(raw_doc_name)
        if "/" in doc_name or "\\" in doc_name:
            doc_name = doc_name.replace("\\", "/").split("/")[-1]
        for ext in [".pdf", ".docx", ".xlsx", ".pptx", ".md", ".txt", ".csv"]:
            if doc_name.lower().endswith(ext):
                doc_name = doc_name[: -len(ext)]
                break
        if "_" in doc_name and " " not in doc_name:
            doc_name = doc_name.replace("_", " ").title()

        header = f"[TÀI LIỆU {i}: {doc_name} | Vai trò: {role_label} | Mục: {section}]"
        context_parts.append(f"{header}\n{chunk['content']}")

        citation_str = doc_name.strip()
        doc_map[i] = [citation_str]

    full_context = "\n\n=========================================\n\n".join(context_parts)

    # 4. Generate LLM response if API key configured (OpenAI or Gemini Fallback)
    llm_response_text = ""
    if settings.openai_api_key or settings.google_api_key:
        try:
            role_personas = {
                "accounting": (
                    "Bạn là Trợ lý AI chuyên môn Kế toán đại lý VinFast. "
                    "Bạn am hiểu sâu sắc về hệ thống DMS, chứng từ, đặt hàng tồn kho PO, tạo yêu cầu mua sắm PR và các nghiệp vụ kế toán xe máy điện."
                ),
                "sales": (
                    "Bạn là Trợ lý AI chuyên môn Tư vấn Bán hàng VinFast. "
                    "Bạn am hiểu sâu sắc về quy trình tư vấn 7 bước, các gói ưu đãi giá, hỗ trợ lệ phí trước bạ, chính sách sạc và thuê pin xe máy điện."
                ),
                "technician": (
                    "Bạn là Trợ lý AI Kỹ thuật viên xưởng dịch vụ VinFast. "
                    "Bạn am hiểu sâu sắc về quy trình sửa chữa pin xe máy điện, bảo dưỡng định kỳ, kiểm tra 5 hạng mục trọng yếu và xử lý lỗi kỹ thuật."
                ),
                "owner": (
                    "Bạn là Trợ lý AI Cố vấn Điều hành & Quản trị Đại trị VinFast. "
                    "Bạn hỗ trợ quản lý tổng thể quy trình liên phòng ban Kế toán, Bán hàng và Kỹ thuật."
                ),
            }
            persona_desc = role_personas.get(
                user_role, "Bạn là Trợ lý AI tư vấn tài liệu nội bộ VinFast (VF AI Onboarding Agent)."
            )

            system_prompt = (
                f"{persona_desc}\n"
                "Hãy trả lời câu hỏi dựa CHÍNH XÁC và CHỈ DỰA VÀO các đoạn văn bản ngữ cảnh dưới đây.\n\n"
                "QUY TẮC BẢO TOÀN DỮ LIỆU & CHỐNG BỊA ĐẶT (ZERO-HALLUCINATION - BẮT BUỘC TUÂN THỦ):\n"
                "1. BẢNG GIÁ & CON SỐ: Chỉ trích dẫn đúng con số, giá tiền (VNĐ), thông số kỹ thuật xuất hiện NGUYÊN VĂN trong [TÀI LIỆU]. TUYỆT ĐỐI KHÔNG tự bịa, suy đoán hoặc ngoại suy giá xe.\n"
                "2. MẪU XE CỤ THỂ: Nếu người dùng hỏi giá hoặc thông số của mẫu xe cụ thể (ví dụ: Evo200, Feliz S, Klara S, Theon S, Vento S...), chỉ trả lời khi tài liệu có đúng mẫu xe đó. Nếu tài liệu không đề cập đến mẫu xe người dùng hỏi, BẮT BUỘC trả lời: 'Hiện tài liệu được cấp quyền chưa có thông tin về mẫu xe [Tên mẫu xe].'\n"
                "3. BẢNG BIỂU: Khi trích xuất bảng giá xe hoặc bảng thông số kỹ thuật, hãy TRÌNH BÀY DƯỚI DẠNG MARKDOWN TABLE (| Cột 1 | Cột 2 |) chuẩn xác, giữ nguyên các cột giá mua pin, giá thuê pin, cọc pin.\n"
                "4. NGUYÊN TẮC TỔNG HỢP: Nếu nguồn là VIDEO (transcript từ MM:SS), hãy tổng hợp thành hướng dẫn bước-by-bước theo thứ tự thời gian. KHÔNG liệt kê timestamp riêng lẻ.\n"
                "- Nếu có nhiều tài liệu từ các nguồn KHÁC NHAU: tổng hợp theo chủ đề, không liệt kê từng tài liệu riêng lẻ.\n"
                '- Chỉ khi hoàn toàn không có bất kỳ thông tin nào liên quan thì mới trả lời: "Không tìm thấy thông tin phù hợp trong tài liệu được cấp quyền."\n\n'
                "YÊU CẦU TRÍCH DẪN NGUỒN:\n"
                "- Ở DÒNG CUỐI CÙNG CỦA PHẢN HỒI, bạn BẮT BUỘC phải ghi danh sách chỉ số các [TÀI LIỆU i] mà bạn ĐÃ THỰC SỰ SỬ DỤNG thông tin theo cú pháp: `[USED_DOCS: 1, 2]`\n"
                "- Nếu không tìm thấy thông tin phù hợp hoặc không dùng tài liệu nào, BẮT BUỘC ghi: `[USED_DOCS: NONE]`.\n"
                "- Trả lời rõ ràng, đầy đủ ý, trích dẫn bảng biểu hoặc con số chính xác nếu có.\n"
                "- Định dạng phản hồi bằng Markdown sạch sẽ.\n\n"
                f"================ CONTEXT BẮT ĐẦU ================\n"
                f"{full_context}\n"
                f"================ CONTEXT KẾT THÚC ================"
            )
            llm = get_llm()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_query},
            ]
            res = await llm.ainvoke(messages)
            llm_response_text = res.content
        except Exception as e:
            logger.warning(f"LLM generation warning: {e}. Using structured context fallback.")

    if not llm_response_text:
        llm_response_text = full_context

    # Numerical grounding check
    money_pattern = r"\b\d{1,3}(?:\.\d{3})+(?:\s*(?:VNĐ|vnd|đ|đồng))?|\b\d+(?:,\d+)?\s*(?:triệu|tỷ)\b"
    response_numbers = re.findall(money_pattern, llm_response_text, re.IGNORECASE)
    unverified = []
    for num in response_numbers:
        digits_only = re.sub(r"[^\d]", "", num)
        if len(digits_only) >= 4 and digits_only not in re.sub(r"[^\d]", "", full_context):
            unverified.append(num)
    if unverified:
        logger.warning(f"Numerical Verifier: Phát hiện số liệu không nằm trong context: {unverified}")

    # 5. Parse USED_DOCS tag and clean up citations
    final_citations: list[str] = []

    needs_escalation = False

    match = re.search(r"\[USED_DOCS:\s*([^\]]+)\]", llm_response_text, re.IGNORECASE)
    used_tag = ""
    if match:
        used_tag = match.group(1).strip()
        # Remove the tag line from response text so user sees clean Markdown
        llm_response_text = re.sub(r"\n?\s*\[USED_DOCS:\s*[^\]]+\]", "", llm_response_text).strip()

        if used_tag.upper() != "NONE":
            parts = used_tag.split(",")
            for p in parts:
                p_str = p.strip()
                if p_str.isdigit():
                    idx = int(p_str)
                    if idx in doc_map:
                        for cite in doc_map[idx]:
                            if cite not in final_citations:
                                final_citations.append(cite)

    no_info_phrases = [
        "không tìm thấy thông tin phù hợp",
        "không tìm thấy tài liệu liên quan",
        "không có thông tin",
    ]
    is_no_info = any(phrase in llm_response_text.lower() for phrase in no_info_phrases)

    if is_no_info or used_tag.upper() == "NONE":
        final_citations = []
        needs_escalation = True
    elif not match and not is_no_info:
        # Fallback heuristic if LLM omitted tag: check if doc title/section is mentioned
        for idx, cite_list in doc_map.items():
            for cite_item in cite_list:
                clean_title = cite_item.split(" (")[0]
                if clean_title.lower() in llm_response_text.lower():
                    if cite_item not in final_citations:
                        final_citations.append(cite_item)
        if not final_citations and doc_map:
            # Fallback to doc 0 (if existing citations) or first chunk
            first_key = next(iter(doc_map))
            final_citations = list(doc_map[first_key])

    # 6. Build retrieved_docs_detail — dành cho frontend source badges
    retrieved_docs_detail = [_build_doc_detail(chunk) for chunk in top_chunks]

    # Determine confidence score
    top_score = top_chunks[0].get("rerank_score", top_chunks[0].get("rrf_score", 0.8))
    rag_confidence = min(max(float(top_score if isinstance(top_score, float) else 0.8), 0.5), 0.99)
    if is_no_info:
        rag_confidence = 0.2

    return {
        "context": llm_response_text,
        "retrieved_docs": top_chunks,
        "retrieved_docs_detail": retrieved_docs_detail,
        "citations": final_citations,
        "rag_confidence": rag_confidence,
        "needs_escalation": needs_escalation,
    }
