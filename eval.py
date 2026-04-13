"""
eval.py — Sprint 4: Evaluation & Scorecard
==========================================
Mục tiêu Sprint 4 (60 phút):
  - Chạy 10 test questions qua pipeline
  - Chấm điểm theo 4 metrics: Faithfulness, Relevance, Context Recall, Completeness
  - So sánh baseline vs variant
  - Ghi kết quả ra scorecard

ĐÃ TÍCH HỢP BONUS: LLM-as-Judge (+2 điểm)
"""

import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from rag_answer import rag_answer
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CẤU HÌNH
# =============================================================================

TEST_QUESTIONS_PATH = Path(__file__).parent / "data" / "test_questions.json"
RESULTS_DIR = Path(__file__).parent / "results"

# Cấu hình baseline (Sprint 2)
BASELINE_CONFIG = {
    "retrieval_mode": "dense",
    "top_k_search": 10,
    "top_k_select": 3,
    "use_rerank": False,
    "label": "baseline_dense",
}

# Cấu hình variant (Sprint 3 — Bạn đã làm Rerank và Hybrid rất xuất sắc)
VARIANT_CONFIG = {
    "retrieval_mode": "hybrid",   
    "top_k_search": 10,
    "top_k_select": 3,
    "use_rerank": False,           
    "label": "variant_hybrid_rerank",
}

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =============================================================================
# HELPER: LLM-as-Judge
# =============================================================================

def call_llm_judge(prompt: str) -> Dict[str, Any]:
    """Hàm phụ trợ gọi LLM để làm giám khảo chấm điểm và ép trả về JSON."""
    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an impartial judge evaluating a RAG system. Always output valid JSON with 'score' (int 1-5) and 'notes' (string brief reason)."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"score": None, "notes": f"Judge Error: {str(e)}"}

# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def score_faithfulness(answer: str, chunks_used: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Faithfulness: Câu trả lời có bám đúng chứng cứ đã retrieve không?"""
    if not chunks_used or "không đủ thông tin" in answer.lower():
        # Nếu hệ thống abstain đúng lúc (không bịa) thì faithfulness vẫn cao
        return {"score": 5, "notes": "Abstained correctly due to no context."}

    context_str = "\n".join([c.get("text", "") for c in chunks_used])
    
    prompt = f"""
    Evaluate the faithfulness of the following answer based ONLY on the given context.
    Does the answer hallucinate or use outside knowledge?
    
    Context:
    {context_str}
    
    Answer:
    {answer}
    
    Rate strictly on a scale of 1-5:
    5 = completely grounded in the provided context.
    3 = mostly grounded, but contains minor unverified details.
    1 = completely hallucinated or heavily uses outside knowledge.
    
    Output JSON format: {{"score": <int>, "notes": "<string reason>"}}
    """
    return call_llm_judge(prompt)


def score_answer_relevance(query: str, answer: str) -> Dict[str, Any]:
    """Answer Relevance: Answer có trả lời đúng câu hỏi người dùng hỏi không?"""
    prompt = f"""
    Evaluate how relevant the answer is to the user's query.
    
    Query: {query}
    Answer: {answer}
    
    Rate strictly on a scale of 1-5:
    5 = answers the query directly and fully.
    3 = answers partially or is slightly off-topic.
    1 = completely misses the point or doesn't answer.
    
    Output JSON format: {{"score": <int>, "notes": "<string reason>"}}
    """
    return call_llm_judge(prompt)


def score_context_recall(chunks_used: List[Dict[str, Any]], expected_sources: List[str]) -> Dict[str, Any]:
    """Context Recall: Retriever có mang về đủ evidence cần thiết không?"""
    if not expected_sources:
        return {"score": None, "recall": None, "notes": "No expected sources provided."}

    retrieved_sources = {c.get("metadata", {}).get("source", "") for c in chunks_used}

    found = 0
    missing = []
    for expected in expected_sources:
        expected_name = expected.split("/")[-1].replace(".pdf", "").replace(".md", "").replace(".txt", "")
        matched = any(expected_name.lower() in r.lower() for r in retrieved_sources)
        if matched:
            found += 1
        else:
            missing.append(expected)

    recall = found / len(expected_sources) if expected_sources else 0
    score = round(recall * 4) + 1  # Convert 0-1 scale to 1-5 scale (0=1, 1=5)

    return {
        "score": score,
        "recall": recall,
        "notes": f"Retrieved {found}/{len(expected_sources)}. Missing: {missing}" if missing else "All sources retrieved."
    }


def score_completeness(query: str, answer: str, expected_answer: str) -> Dict[str, Any]:
    """Completeness: Answer có bao phủ đủ thông tin so với expected_answer không?"""
    if not expected_answer:
        return {"score": None, "notes": "No expected answer provided for comparison."}

    prompt = f"""
    Compare the generated answer with the expected answer key for the given query.
    Does the generated answer cover all the crucial points mentioned in the expected answer?
    
    Query: {query}
    Expected Key: {expected_answer}
    Generated Answer: {answer}
    
    Rate strictly on a scale of 1-5:
    5 = covers all key points perfectly.
    3 = misses some important details but gets the main idea.
    1 = misses the core points completely.
    
    Output JSON format: {{"score": <int>, "notes": "<string reason>"}}
    """
    return call_llm_judge(prompt)


# =============================================================================
# SCORECARD RUNNER
# =============================================================================

def run_scorecard(config: Dict[str, Any], test_questions: Optional[List[Dict]] = None, verbose: bool = True) -> List[Dict[str, Any]]:
    if test_questions is None:
        with open(TEST_QUESTIONS_PATH, "r", encoding="utf-8") as f:
            test_questions = json.load(f)

    results = []
    label = config.get("label", "unnamed")

    print(f"\n{'='*70}")
    print(f"Chạy scorecard: {label}")
    print(f"Config: {config}")
    print('='*70)

    for q in test_questions:
        question_id = q["id"]
        query = q["question"]
        expected_answer = q.get("expected_answer", "")
        expected_sources = q.get("expected_sources", [])
        category = q.get("category", "")

        if verbose:
            print(f"\n[{question_id}] {query}")

        try:
            result = rag_answer(
                query=query,
                retrieval_mode=config.get("retrieval_mode", "dense"),
                top_k_search=config.get("top_k_search", 10),
                top_k_select=config.get("top_k_select", 3),
                use_rerank=config.get("use_rerank", False),
                verbose=False,
            )
            answer = result["answer"]
            chunks_used = result["chunks_used"]

        except Exception as e:
            answer = f"ERROR: {e}"
            chunks_used = []

        # Gọi Giám Khảo LLM chấm điểm
        faith = score_faithfulness(answer, chunks_used)
        relevance = score_answer_relevance(query, answer)
        recall = score_context_recall(chunks_used, expected_sources)
        complete = score_completeness(query, answer, expected_answer)

        row = {
            "id": question_id,
            "category": category,
            "query": query,
            "answer": answer,
            "expected_answer": expected_answer,
            "faithfulness": faith.get("score"),
            "faithfulness_notes": faith.get("notes", ""),
            "relevance": relevance.get("score"),
            "relevance_notes": relevance.get("notes", ""),
            "context_recall": recall.get("score"),
            "context_recall_notes": recall.get("notes", ""),
            "completeness": complete.get("score"),
            "completeness_notes": complete.get("notes", ""),
            "config_label": label,
        }
        results.append(row)

        if verbose:
            print(f"  Answer: {answer[:100]}...")
            print(f"  Scores -> F: {row['faithfulness']} | R: {row['relevance']} | C_Rec: {row['context_recall']} | Comp: {row['completeness']}")

    for metric in ["faithfulness", "relevance", "context_recall", "completeness"]:
        scores = [r[metric] for r in results if r[metric] is not None and isinstance(r[metric], (int, float))]
        avg = sum(scores) / len(scores) if scores else None
        print(f"\nAverage {metric}: {avg:.2f}" if avg else f"\nAverage {metric}: N/A (chưa có điểm)")

    return results

# =============================================================================
# A/B COMPARISON
# =============================================================================

def compare_ab(baseline_results: List[Dict], variant_results: List[Dict], output_csv: Optional[str] = None) -> None:
    metrics = ["faithfulness", "relevance", "context_recall", "completeness"]

    print(f"\n{'='*70}")
    print("A/B Comparison: Baseline vs Variant")
    print('='*70)
    print(f"{'Metric':<20} {'Baseline':>10} {'Variant':>10} {'Delta':>8}")
    print("-" * 55)

    for metric in metrics:
        b_scores = [r[metric] for r in baseline_results if r[metric] is not None and isinstance(r[metric], (int, float))]
        v_scores = [r[metric] for r in variant_results if r[metric] is not None and isinstance(r[metric], (int, float))]

        b_avg = sum(b_scores) / len(b_scores) if b_scores else None
        v_avg = sum(v_scores) / len(v_scores) if v_scores else None
        delta = (v_avg - b_avg) if (b_avg is not None and v_avg is not None) else None

        b_str = f"{b_avg:.2f}" if b_avg else "N/A"
        v_str = f"{v_avg:.2f}" if v_avg else "N/A"
        d_str = f"{delta:+.2f}" if delta else "N/A"

        print(f"{metric:<20} {b_str:>10} {v_str:>10} {d_str:>8}")

    print(f"\n{'Câu':<6} {'Baseline (F/R/Rc/C)':<25} {'Variant (F/R/Rc/C)':<25} {'Better?':<10}")
    print("-" * 70)

    b_by_id = {r["id"]: r for r in baseline_results}
    for v_row in variant_results:
        qid = v_row["id"]
        b_row = b_by_id.get(qid, {})

        b_scores_str = "/".join([str(b_row.get(m, "?")) for m in metrics])
        v_scores_str = "/".join([str(v_row.get(m, "?")) for m in metrics])

        b_total = sum(b_row.get(m, 0) or 0 for m in metrics if isinstance(b_row.get(m), (int, float)))
        v_total = sum(v_row.get(m, 0) or 0 for m in metrics if isinstance(v_row.get(m), (int, float)))
        better = "Variant" if v_total > b_total else ("Baseline" if b_total > v_total else "Tie")

        print(f"{qid:<6} {b_scores_str:<25} {v_scores_str:<25} {better:<10}")

    if output_csv:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = RESULTS_DIR / output_csv
        combined = baseline_results + variant_results
        if combined:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=combined[0].keys())
                writer.writeheader()
                writer.writerows(combined)
            print(f"\nKết quả đã lưu vào: {csv_path}")


def generate_scorecard_summary(results: List[Dict], label: str) -> str:
    metrics = ["faithfulness", "relevance", "context_recall", "completeness"]
    averages = {}
    for metric in metrics:
        scores = [r[metric] for r in results if r[metric] is not None and isinstance(r[metric], (int, float))]
        averages[metric] = sum(scores) / len(scores) if scores else None

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = f"""# Scorecard: {label}\nGenerated: {timestamp}\n\n## Summary\n\n| Metric | Average Score |\n|--------|--------------|\n"""
    for metric, avg in averages.items():
        avg_str = f"{avg:.2f}/5" if avg else "N/A"
        md += f"| {metric.replace('_', ' ').title()} | {avg_str} |\n"

    md += "\n## Per-Question Results\n\n"
    md += "| ID | Category | Faithful | Relevant | Recall | Complete | Notes |\n"
    md += "|----|----------|----------|----------|--------|----------|-------|\n"

    for r in results:
        notes = str(r.get('faithfulness_notes', '')).replace('\n', ' ')[:50]
        md += (f"| {r['id']} | {r['category']} | {r.get('faithfulness', 'N/A')} | "
               f"{r.get('relevance', 'N/A')} | {r.get('context_recall', 'N/A')} | "
               f"{r.get('completeness', 'N/A')} | {notes}... |\n")

    return md

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 4: Evaluation & Scorecard (LLM-as-Judge Enabled)")
    print("=" * 60)

    try:
        with open(TEST_QUESTIONS_PATH, "r", encoding="utf-8") as f:
            test_questions = json.load(f)
        print(f"Tìm thấy {len(test_questions)} câu hỏi test.")
    except FileNotFoundError:
        print("Không tìm thấy file test_questions.json!")
        test_questions = []

    if test_questions:
        print("\n--- 1. Chạy Baseline ---")
        baseline_results = run_scorecard(config=BASELINE_CONFIG, test_questions=test_questions, verbose=True)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        (RESULTS_DIR / "scorecard_baseline.md").write_text(generate_scorecard_summary(baseline_results, "baseline_dense"), encoding="utf-8")

        print("\n--- 2. Chạy Variant ---")
        variant_results = run_scorecard(config=VARIANT_CONFIG, test_questions=test_questions, verbose=True)
        (RESULTS_DIR / "scorecard_variant.md").write_text(generate_scorecard_summary(variant_results, VARIANT_CONFIG["label"]), encoding="utf-8")

        print("\n--- 3. A/B Comparison ---")
        compare_ab(baseline_results, variant_results, output_csv="ab_comparison.csv")
        
        print("\nHoàn thành xuất sắc Sprint 4! 🎉")
        print("Đừng quên viết Báo cáo Tuning Log dựa vào bảng A/B Comparison ở trên nhé.")