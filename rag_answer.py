"""
rag_answer.py — Sprint 2 + Sprint 3: Retrieval & Grounded Answer
================================================================
Sprint 2 (60 phút): Baseline RAG
  - Dense retrieval từ ChromaDB
  - Grounded answer function với prompt ép citation
  - Trả lời được ít nhất 3 câu hỏi mẫu, output có source

Sprint 3 (60 phút): Tuning tối thiểu
  - Thêm hybrid retrieval (dense + sparse/BM25)
  - Hoặc thêm rerank (cross-encoder)
  - Hoặc thử query transformation (expansion, decomposition, HyDE)
  - Tạo bảng so sánh baseline vs variant

Definition of Done Sprint 2:
  ✓ rag_answer("SLA ticket P1?") trả về câu trả lời có citation
  ✓ rag_answer("Câu hỏi không có trong docs") trả về "Không đủ dữ liệu"

Definition of Done Sprint 3:
  ✓ Có ít nhất 1 variant (hybrid / rerank / query transform) chạy được
  ✓ Giải thích được tại sao chọn biến đó để tune
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

import chromadb
from openai import OpenAI
from index import get_embedding, CHROMA_DB_DIR
from rank_bm25 import BM25Okapi 
from sentence_transformers import CrossEncoder
from pyvi import ViTokenizer  # Thêm thư viện tách từ Tiếng Việt

load_dotenv()

# =============================================================================
# CẤU HÌNH
# =============================================================================

TOP_K_SEARCH = 10    # Số chunk lấy từ vector store trước rerank (search rộng)
TOP_K_SELECT = 3     # Số chunk gửi vào prompt sau rerank/select (top-3 sweet spot)

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# =============================================================================
# CACHE CHO BM25 (Giải quyết nút thắt cổ chai hiệu năng)
# =============================================================================
_bm25_index = None
_bm25_corpus_data = None  # Lưu trữ ID, Text và Metadata để truy xuất nhanh

def init_bm25():
    """Khởi tạo và cache BM25 Index một lần duy nhất."""
    global _bm25_index, _bm25_corpus_data
    if _bm25_index is not None:
        return

    print("  [BM25] Đang khởi tạo và tokenize corpus tiếng Việt...")
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection("rag_lab")
    
    # Kéo toàn bộ dữ liệu ra (mặc định lấy được cả 'ids')
    all_data = collection.get(include=["documents", "metadatas"])
    
    _bm25_corpus_data = []
    tokenized_corpus = []
    
    for i in range(len(all_data["documents"])):
        doc_id = all_data["ids"][i]
        text = all_data["documents"][i]
        meta = all_data["metadatas"][i]
        
        # Lưu lại bản gốc kèm ID
        _bm25_corpus_data.append({"id": doc_id, "text": text, "metadata": meta})
        
        # Tách từ tiếng Việt bằng pyvi (VD: "hỗ trợ" -> "hỗ_trợ")
        tokenized_text = ViTokenizer.tokenize(text).lower().split()
        tokenized_corpus.append(tokenized_text)
        
    _bm25_index = BM25Okapi(tokenized_corpus)
    print("  [BM25] Khởi tạo xong!")


# =============================================================================
# RETRIEVAL — DENSE (Vector Search)
# =============================================================================

def retrieve_dense(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    """
    Dense retrieval: tìm kiếm theo embedding similarity trong ChromaDB.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection("rag_lab")

    query_embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "id": results["ids"][0][i], # THÊM TRƯỜNG ID
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "score": 1 - results["distances"][0][i] # Chuyển distance thành similarity
        })
    return chunks


# =============================================================================
# RETRIEVAL — SPARSE / BM25 (Keyword Search)
# =============================================================================

def retrieve_sparse(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    """
    Sparse retrieval: tìm kiếm theo keyword (BM25) với Cache và Tokenizer.
    """
    global _bm25_index, _bm25_corpus_data
    
    # Load cache nếu chưa có (chỉ tốn thời gian ở câu hỏi đầu tiên)
    if _bm25_index is None:
        init_bm25()
    
    # Tách từ câu query chuẩn tiếng Việt
    tokenized_query = ViTokenizer.tokenize(query).lower().split()
    doc_scores = _bm25_index.get_scores(tokenized_query)
    
    top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
    
    # Trả về kết quả từ cache, không cần gọi lại ChromaDB
    results = []
    for i in top_indices:
        doc = _bm25_corpus_data[i].copy() # Copy để không đè score gốc
        doc["score"] = float(doc_scores[i])
        results.append(doc)
        
    return results


# =============================================================================
# RETRIEVAL — HYBRID (Dense + Sparse với Reciprocal Rank Fusion)
# =============================================================================

def retrieve_hybrid(
    query: str,
    top_k: int = TOP_K_SEARCH,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval: kết hợp dense và sparse bằng Reciprocal Rank Fusion (RRF).
    Sử dụng Chunk ID để mapping an toàn.
    """
    dense_results = retrieve_dense(query, top_k=top_k)
    sparse_results = retrieve_sparse(query, top_k=top_k)
    
    # Reciprocal Rank Fusion (RRF) dùng ID làm khóa chính
    rrf_scores = {}
    
    for rank, doc in enumerate(dense_results):
        doc_id = doc["id"]
        # Nhân thêm hệ số dense_weight để tinh chỉnh độ ưu tiên
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + dense_weight * (1.0 / (60 + rank))
        
    for rank, doc in enumerate(sparse_results):
        doc_id = doc["id"]
        # Nhân thêm hệ số sparse_weight
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + sparse_weight * (1.0 / (60 + rank))
        
    # Sắp xếp lại dựa trên RRF score cao nhất
    sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    # Gom tất cả chunks vào một dictionary để tra cứu ngược (Look-up) cực nhanh bằng ID
    all_results = {doc["id"]: doc for doc in dense_results + sparse_results}
    
    final_results = []
    for doc_id, _ in sorted_ids:
        final_results.append(all_results[doc_id])
        
    return final_results


# =============================================================================
# RERANK
# =============================================================================

def rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = TOP_K_SELECT,
) -> List[Dict[str, Any]]:
    """
    Rerank các candidate chunks bằng cross-encoder.
    """
    if not candidates:
        return []
    
    # Logic: Dùng cross-encoder BAAI/bge-reranker-v2-m3 cho Vietnamese
    model = CrossEncoder("BAAI/bge-reranker-v2-m3")
    pairs = [[query, c["text"]] for c in candidates]
    scores = model.predict(pairs)
    for i, chunk in enumerate(candidates):
        chunk["rerank_score"] = float(scores[i])
    candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

    return candidates[:top_k]


# =============================================================================
# QUERY TRANSFORMATION
# =============================================================================

def transform_query(query: str, strategy: str = "expansion") -> List[str]:
    """
    Biến đổi query để tăng recall (Sử dụng LLM sinh thêm từ đồng nghĩa).
    """
    if strategy != "expansion":
        return [query]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"Given the Vietnamese query: '{query}', generate 2 alternative phrasings in Vietnamese. Output as JSON array of strings: [\"q1\", \"q2\"]"

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        expanded = next((v for v in data.values() if isinstance(v, list)), [])
        return [query] + expanded
    except:
        return [query]


# =============================================================================
# GENERATION — GROUNDED ANSWER FUNCTION
# =============================================================================

def build_context_block(chunks: List[Dict[str, Any]]) -> str:
    """
    Đóng gói danh sách chunks thành context block để đưa vào prompt.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        section = meta.get("section", "")
        score = chunk.get("score", 0)
        text = chunk.get("text", "")

        header = f"[{source}]"
        if section:
            header += f" | {section}"
        if meta.get("department"):
            header += f" | Dept: {meta['department']}"
        if meta.get("effective_date"):
            header += f" | Date: {meta['effective_date']}"
        if score > 0:
            header += f" | score={score:.2f}"

        context_parts.append(f"{header}\n{text}")

    return "\n\n".join(context_parts)


def build_grounded_prompt(query: str, context_block: str) -> str:
    """
    Xây dựng grounded prompt với quy tắc thép để chống Hallucination và ép Citation.
    """
    prompt = f"""Bạn là một trợ lý AI nội bộ của công ty. Nhiệm vụ của bạn là trả lời câu hỏi CHỈ DỰA TRÊN NGỮ CẢNH ĐƯỢC CUNG CẤP.

CÁC QUY TẮC TỐI THƯỢNG (PHẢI TUÂN THỦ):
1. CHỐNG BỊA ĐẶT: Nếu trong ngữ cảnh hoàn toàn không có thông tin để trả lời, PHẢI trả lời ĐÚNG một câu: "Tôi không biết."
2. TRÍCH DẪN RÕ RÀNG: Ở cuối mỗi ý, tuyệt đối KHÔNG CHỈ GHI [1], [2]. Bạn PHẢI ghi đích danh tên file nguồn vào trong ngoặc vuông. 
   - Ví dụ SAI: "SLA là 4 giờ [1]."
   - Ví dụ ĐÚNG: "SLA là 4 giờ [support/sla-p1-2026.pdf]."
3. ĐẦY ĐỦ (COMPLETENESS): Đọc kỹ câu hỏi xem có bao nhiêu vế (Ví dụ: cái gì, bao lâu, ở đâu, ai duyệt). Phải trả lời ĐẦY ĐỦ TẤT CẢ các vế được hỏi. Đừng bỏ sót chi tiết.
4. THỜI GIAN: Nếu tài liệu có nhắc đến phiên bản (version) hoặc ngày hiệu lực, bắt buộc phải đưa vào câu trả lời để làm rõ ngữ cảnh.
5. NGÔN NGỮ: Tiếng Việt.

Ngữ cảnh (Context):
{context_block}

Câu hỏi (Question): {query}

Trả lời (Answer):"""
    return prompt


def call_llm(prompt: str) -> str:
    """
    Gọi LLM để sinh câu trả lời.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=512,
    )
    return response.choices[0].message.content


def rag_answer(
    query: str,
    retrieval_mode: str = "dense",
    top_k_search: int = TOP_K_SEARCH,
    top_k_select: int = TOP_K_SELECT,
    use_rerank: bool = False,
    use_transform: bool = False,               
    transform_strategy: str = "expansion",
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Pipeline RAG hoàn chỉnh: query → retrieve → (rerank) → generate.
    """
    config = {
        "retrieval_mode": retrieval_mode,
        "top_k_search": top_k_search,
        "top_k_select": top_k_select,
        "use_rerank": use_rerank,
        "use_transform": use_transform,       
        "transform_strategy": transform_strategy, # Đã xóa dòng ghi đè lỗi ở đây
    }
    
    queries = transform_query(query, strategy=transform_strategy) if config["use_transform"] else [query]

    # --- Bước 1: Retrieve ---
    all_candidates = []
    for q in queries:
        if retrieval_mode == "dense":
            all_candidates.extend(retrieve_dense(q, top_k=top_k_search))
        elif retrieval_mode == "sparse":
            all_candidates.extend(retrieve_sparse(q, top_k=top_k_search))
        elif retrieval_mode == "hybrid":
            all_candidates.extend(retrieve_hybrid(q, top_k=top_k_search))
        else:
            raise ValueError(f"retrieval_mode không hợp lệ: {retrieval_mode}")

    # Loại bỏ trùng lặp
    seen = set()
    candidates = []
    for c in all_candidates:
        if c["text"] not in seen:
            candidates.append(c)
            seen.add(c["text"])

    if verbose:
        print(f"\n[RAG] Query: {query}")
        print(f"[RAG] Retrieved {len(candidates)} unique candidates (mode={retrieval_mode})")

    # --- Bước 2: Rerank (optional) ---
    if use_rerank:
        candidates = rerank(query, candidates, top_k=top_k_select)
    else:
        candidates = candidates[:top_k_select]

    if verbose:
        print(f"[RAG] After select: {len(candidates)} chunks")

    # --- Bước 3: Build context và prompt ---
    context_block = build_context_block(candidates)
    prompt = build_grounded_prompt(query, context_block)

    if verbose:
        print(f"\n[RAG] Prompt:\n{prompt[:500]}...\n")

    # --- Bước 4: Generate ---
    answer = call_llm(prompt)

    # --- Bước 5: Extract sources ---
    sources = list({
        c["metadata"].get("source", "unknown")
        for c in candidates
    })

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "chunks_used": candidates,
        "config": config,
    }


# =============================================================================
# SPRINT 3: SO SÁNH BASELINE VS VARIANT
# =============================================================================

def compare_retrieval_strategies(query: str) -> None:
    """So sánh các retrieval strategies với cùng một query."""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print('='*60)

    strategies = ["dense", "hybrid"]

    for strategy in strategies:
        print(f"\n--- Strategy: {strategy} ---")
        try:
            result = rag_answer(query, retrieval_mode=strategy, verbose=False)
            print(f"Answer: {result['answer']}")
            print(f"Sources: {result['sources']}")
        except NotImplementedError as e:
            print(f"Chưa implement: {e}")
        except Exception as e:
            print(f"Lỗi: {e}")


# =============================================================================
# MAIN — Demo và Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 2 + 3: RAG Answer Pipeline")
    print("=" * 60)

    # Test queries từ data/test_questions.json
    test_queries = [
        "SLA xử lý ticket P1 là bao lâu?",
        "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?",
        "Ai phải phê duyệt để cấp quyền Level 3?",
        "ERR-403-AUTH là lỗi gì?",  # Query không có trong docs → kiểm tra abstain
    ]

    print("\n--- Sprint 2: Test Baseline (Dense) ---")
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            result = rag_answer(query, retrieval_mode="dense", verbose=True)
            print(f"Answer: {result['answer']}")
            print(f"Sources: {result['sources']}")
        except NotImplementedError:
            print("Chưa implement — hoàn thành TODO trong retrieve_dense() và call_llm() trước.")
        except Exception as e:
            print(f"Lỗi: {e}")

    # --- Sprint 3: So sánh strategies ---
    compare_retrieval_strategies("SLA xử lý ticket P1 là bao lâu?")
    compare_retrieval_strategies("Ai phải phê duyệt để cấp quyền Level 3?")