import pytest
import re
from rag_answer import (
    rag_answer, 
    build_context_block, 
    retrieve_dense, 
    retrieve_sparse, 
    retrieve_hybrid
)

# =============================================================================
# SPRINT 2 TESTS: Baseline RAG
# =============================================================================

def test_rag_answer_with_citation():
    """
    Kiểm tra: RAG trả lời câu hỏi có trong docs và có kèm trích dẫn [1].
    """
    query = "SLA xử lý ticket P1 là bao lâu?"
    result = rag_answer(query, retrieval_mode="dense", top_k_search=5, top_k_select=3)
    
    answer = result["answer"]
    sources = result["sources"]
    
    assert answer is not None and len(answer) > 0, "Câu trả lời không được để trống."
    assert len(sources) > 0, "Phải trích dẫn ít nhất 1 source."
    
    # Kiểm tra xem AI có ngoan ngoãn đặt số [1], [2] vào câu trả lời không
    has_citation = bool(re.search(r"\[\d+\]", answer))
    assert has_citation, f"Thiếu trích dẫn dạng [1]. Câu trả lời của AI: {answer}"

def test_rag_answer_abstain_on_missing_context():
    """
    Kiểm tra: Tránh Hallucination. Câu hỏi ngoài luồng phải bị từ chối.
    Prompt gốc của bạn ghi: "Nếu ngữ cảnh không đủ, hãy nói bạn không biết."
    """
    query = "Hướng dẫn chi tiết cách nấu thịt kho hột vịt?"
    result = rag_answer(query, retrieval_mode="dense", top_k_search=3, top_k_select=2)
    
    answer = result["answer"].lower()
    
    # Kiểm tra xem AI có tuân thủ lệnh "nói bạn không biết" không
    is_abstained = "không biết" in answer or "không có thông tin" in answer or "không đề cập" in answer
    assert is_abstained, f"AI bịa câu trả lời thay vì từ chối. Câu trả lời của AI: {answer}"

def test_build_context_block_format():
    """
    Kiểm tra: Hàm build_context_block chuẩn bị prompt đúng format.
    """
    dummy_chunks = [
        {"metadata": {"source": "policy.pdf", "section": "S1"}, "score": 0.9, "text": "Text A"},
    ]
    
    context = build_context_block(dummy_chunks)
    
    assert "[1] policy.pdf | S1" in context
    assert "Text A" in context


# =============================================================================
# SPRINT 3 TESTS: Variant Tuning
# =============================================================================

def test_sparse_retrieval_returns_results():
    """
    Kiểm tra: Sparse (BM25) build trên RAM và trả kết quả thành công.
    Phiên bản này của bạn trả về: text, metadata, score.
    """
    query = "VPN"
    results = retrieve_sparse(query, top_k=3)
    
    assert len(results) > 0
    assert "text" in results[0]
    assert "score" in results[0]
    assert "metadata" in results[0]

def test_hybrid_retrieval_returns_results():
    """
    Kiểm tra: Hybrid (Dense + Sparse) dùng RRF và map bằng 'text' chạy không lỗi.
    """
    query = "Quy trình hoàn tiền"
    results = retrieve_hybrid(query, top_k=3, dense_weight=0.5, sparse_weight=0.5)
    
    assert len(results) > 0
    assert "text" in results[0]
    assert "metadata" in results[0]

def test_rag_answer_with_variant_hybrid_and_rerank():
    """
    Kiểm tra: Toàn bộ pipeline End-to-End với cấu hình max settings.
    """
    query = "Mức phạt SLA P1 là bao nhiêu?" # Câu này thực tế ko có phạt trong doc
    
    result = rag_answer(
        query, 
        retrieval_mode="hybrid", 
        use_rerank=True, 
        top_k_search=6, 
        top_k_select=2
    )
    
    assert result["config"]["retrieval_mode"] == "hybrid"
    assert result["config"]["use_rerank"] is True
    assert len(result["chunks_used"]) <= 2
    assert type(result["answer"]) == str