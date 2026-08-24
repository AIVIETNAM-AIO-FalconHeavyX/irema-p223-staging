import pytest

from eval.evaluator import RAGEvaluator
from src.embedding.embedder import EmbeddingService
from src.vectordb.bm25_store import BM25Retriever
from src.vectordb.chroma_store import ChromaVectorStore
from src.vectordb.hybrid_search import HybridRetriever
from src.vectordb.reranker import RerankerService


@pytest.fixture
def sample_chunks():
    return [
        {
            "chunk_id": "SALE001_chunk_001",
            "content": "[Document: Quy trình bán hàng | Role: sales]\n\nQuy trình bán hàng xe máy điện VinFast bao gồm 5 bước cốt lõi.",
            "raw_content": "Quy trình bán hàng xe máy điện VinFast bao gồm 5 bước cốt lõi.",
            "metadata": {
                "document": "Quy trình bán hàng",
                "role": "sales",
                "source": "Sale/quy_trinh.pdf",
                "section": "Quy trình",
            },
        },
        {
            "chunk_id": "KTV001_chunk_001",
            "content": "[Document: Bảo hành | Role: technician]\n\nThời gian bảo hành xe máy điện pin LFP là 6 năm không giới hạn km.",
            "raw_content": "Thời gian bảo hành xe máy điện pin LFP là 6 năm không giới hạn km.",
            "metadata": {
                "document": "Bảo hành",
                "role": "technician",
                "source": "KTV/bao_hanh.pdf",
                "section": "5. Thời gian bảo hành",
            },
        },
        {
            "chunk_id": "GEN001_chunk_001",
            "content": "[Document: Quy định chung | Role: general]\n\nQuy định chung về văn hóa doanh nghiệp Vingroup.",
            "raw_content": "Quy định chung về văn hóa doanh nghiệp Vingroup.",
            "metadata": {
                "document": "Quy định chung",
                "role": "general",
                "source": "General_doc/quy_dinh.pdf",
                "section": "Văn hóa",
            },
        },
    ]


def test_embedding_service():
    service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vec = service.embed_text("Tiêu chuẩn bán hàng VinFast")
    assert len(vec) == 384
    assert isinstance(vec[0], float)

    batch_vecs = service.embed_documents(["Text 1", "Text 2"])
    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 384


def test_chroma_vector_store_and_role_filtering(tmp_path, sample_chunks):
    store_dir = tmp_path / "chroma"
    vector_store = ChromaVectorStore(persist_dir=store_dir, collection_name="test_chunks")
    vector_store.add_chunks(sample_chunks)

    # Query with role='sales' should match sales & general, but NOT technician
    sales_hits = vector_store.query("bán hàng xe máy điện", top_k=5, role="sales")
    assert len(sales_hits) >= 1
    hit_roles = [h["metadata"]["role"] for h in sales_hits]
    assert "technician" not in hit_roles
    assert "sales" in hit_roles


def test_bm25_retriever(tmp_path, sample_chunks):
    index_file = tmp_path / "bm25_test.pkl"
    bm25 = BM25Retriever(index_path=index_file)
    bm25.build_index(sample_chunks)

    hits = bm25.query("bảo hành pin LFP 6 năm", top_k=2, role="technician")
    assert len(hits) >= 1
    assert hits[0]["chunk_id"] == "KTV001_chunk_001"


def test_hybrid_search_and_rrf(tmp_path, sample_chunks):
    store_dir = tmp_path / "chroma_hybrid"
    bm25_file = tmp_path / "bm25_hybrid.pkl"

    vector_store = ChromaVectorStore(persist_dir=store_dir, collection_name="test_hybrid")
    vector_store.add_chunks(sample_chunks)

    bm25 = BM25Retriever(index_path=bm25_file)
    bm25.build_index(sample_chunks)

    hybrid = HybridRetriever(vector_store=vector_store, bm25_retriever=bm25)
    results = hybrid.search("bảo hành pin LFP", top_k=3, role="technician")

    assert len(results) >= 1
    assert "rrf_score" in results[0]
    assert results[0]["chunk_id"] == "KTV001_chunk_001"


def test_reranker():
    reranker = RerankerService(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    candidates = [
        {"chunk_id": "C1", "content": "Tiêu chuẩn diện mạo nhân viên bán hàng"},
        {"chunk_id": "C2", "content": "Thời gian bảo hành pin LFP là 6 năm"},
    ]
    reranked = reranker.rerank("Thời gian bảo hành pin LFP bao nhiêu năm?", candidates, top_k=2)
    # Behavior mới: min_score_threshold filter chunk không liên quan
    # C2 luôn phải là kết quả top (nếu có kết quả)
    assert len(reranked) >= 1, "Phải có nhất 1 kết quả sau reranking"
    assert len(reranked) <= 2, "Tối đa top_k kết quả"
    assert reranked[0]["chunk_id"] == "C2", "Chunk liên quan nhất phải lên top"
    assert reranked[0]["rerank_score"] > 0, "Chunk liên quan phải có score dương"

    # Test explicit: tắt threshold → phải trả về đúng top_k
    reranked_no_filter = reranker.rerank(
        "Thời gian bảo hành pin LFP bao nhiêu năm?",
        candidates,
        top_k=2,
        min_score_threshold=-1000.0,  # Không filter
    )
    assert len(reranked_no_filter) == 2, "Không filter: phải trả đúng top_k"
    assert reranked_no_filter[0]["chunk_id"] == "C2"


def test_rag_evaluator(tmp_path, sample_chunks):
    store_dir = tmp_path / "chroma_eval"
    bm25_file = tmp_path / "bm25_eval.pkl"

    vector_store = ChromaVectorStore(persist_dir=store_dir, collection_name="test_eval")
    vector_store.add_chunks(sample_chunks)

    bm25 = BM25Retriever(index_path=bm25_file)
    bm25.build_index(sample_chunks)

    hybrid = HybridRetriever(vector_store=vector_store, bm25_retriever=bm25)
    reranker = RerankerService()

    evaluator = RAGEvaluator(hybrid_retriever=hybrid, reranker=reranker)

    dataset = [
        {
            "query_id": "Q001",
            "query": "Thời gian bảo hành pin LFP",
            "role": "technician",
            "expected_document_id": "KTV001",
            "expected_section": "5. Thời gian bảo hành",
            "query_type": "table",
        }
    ]

    metrics = evaluator.evaluate(top_k=2, test_cases=dataset)
    assert metrics["hit_rate_at_k"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["role_compliance_rate"] == 1.0
