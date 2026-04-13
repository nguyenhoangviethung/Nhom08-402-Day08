# Implementation Plan - Complete rag_answer.py

The goal is to finalize `rag_answer.py` by implementing the remaining retrieval and generation logic (Sprint 2 & 3), ensuring full integration with `index.py` and `eval.py` without modifying them. The system is designed for Vietnamese data.

## User Review Required

> [!IMPORTANT]
> The system handles Vietnamese data. I will use `BAAI/bge-reranker-v2-m3` for reranking as it performs excellently for Vietnamese and multilingual tasks. I will assume `index.py` and `eval.py` are fully functional as provided in your final environment.

> [!NOTE]
> I will use OpenAI for query transformation (expansion) in Vietnamese.

## Proposed Changes

### [rag_answer.py](file:///home/anhle/vinuni/week_03/Nhom08-402-Day08/rag_answer.py)

#### [MODIFY] [rag_answer.py](file:///home/anhle/vinuni/week_03/Nhom08-402-Day08/rag_answer.py)

1.  **Imports**: 
    - Ensure `OpenAI` and `BM25Okapi` are correctly imported.
    - Add `from sentence_transformers import CrossEncoder` for reranking.
2.  **`retrieve_sparse`**: 
    - Keep current implementation which uses `BM25Okapi`.
3.  **`rerank`**:
    - Implement using `CrossEncoder` with `BAAI/bge-reranker-v2-m3` (Vietnamese support). It will score candidates against the query and return the top-k.
4.  **`transform_query`**:
    - Implement `expansion` strategy using LLM to generate 2-3 alternative phrasings in Vietnamese.
5.  **`build_context_block`**:
    - Update format to include `effective_date`, `department`, and `access` metadata.
6.  **`build_grounded_prompt`**:
    - Refine the prompt to explicitly request answers in Vietnamese and cite sources correctly.
7.  **`rag_answer`**:
    - Integrate `transform_query` to improve recall. When `use_transform=True`, combine results from all queries before reranking.
8.  **Main/Demo**:
    - Uncomment `compare_retrieval_strategies` calls.
    - Clean up all "TODO" comments.

## Verification Plan

### Automated Tests
- Since I cannot modify `index.py`, I will perform a dry run or use a mock if possible to verify the logic in `rag_answer.py`.
- Run `python3 rag_answer.py` to ensure no syntax errors and that the pipeline flow is correct (even if it hits `NotImplementedError` in `index.py` during execution, the logic will be verified).

### Manual Verification
- Verify that the prompt generates citations in the expected format (e.g., `[1]`).
- Verify that "Không đủ dữ liệu" cases are handled when the context is insufficient.
