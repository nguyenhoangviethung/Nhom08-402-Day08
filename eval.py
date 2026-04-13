"""
eval.py - Sprint 4: Evaluation & Scorecard
==========================================

Implements the original lab frame:
- 4 scoring metrics
- baseline vs variant scorecards
- A/B comparison
- grading log export
"""

import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import OpenAI

from rag_answer import rag_answer


# =============================================================================
# CONFIG
# =============================================================================

TEST_QUESTIONS_PATH = Path(__file__).parent / "data" / "test_questions.json"
GRADING_QUESTIONS_PATH = Path(__file__).parent / "data" / "grading_questions.json"
RESULTS_DIR = Path(__file__).parent / "results"
LOGS_DIR = Path(__file__).parent / "logs"

BASELINE_CONFIG = {
    "retrieval_mode": "dense",
    "top_k_search": 10,
    "top_k_select": 3,
    "use_rerank": False,
    "label": "baseline_dense",
}

# Keep only one changed variable for A/B fairness.
VARIANT_CONFIG = {
    "retrieval_mode": "dense",
    "top_k_search": 10,
    "top_k_select": 3,
    "use_rerank": True,
    "label": "variant_dense_rerank",
}

JUDGE_MODEL = os.getenv("JUDGE_MODEL", os.getenv("LLM_MODEL", "gpt-4o-mini"))
_judge_client: Optional[OpenAI] = None


# =============================================================================
# JUDGE HELPERS
# =============================================================================

def _get_judge_client() -> OpenAI:
    global _judge_client
    if _judge_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY for LLM-as-Judge.")
        _judge_client = OpenAI(api_key=api_key)
    return _judge_client


def _build_chunks_text(chunks_used: List[Dict[str, Any]], max_chars: int = 5000) -> str:
    parts = []
    for i, chunk in enumerate(chunks_used, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        section = meta.get("section", "")
        text = chunk.get("text", "")
        header = f"[{i}] {source}"
        if section:
            header += f" | {section}"
        parts.append(f"{header}\n{text}")
    return "\n\n".join(parts)[:max_chars]


def _judge_score(metric_name: str, rubric: str, prompt_body: str) -> Dict[str, Any]:
    try:
        client = _get_judge_client()
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are grading a RAG lab output. "
                        f"Score only the metric '{metric_name}'. "
                        "Return valid JSON with keys: score, notes. "
                        "score must be an integer from 1 to 5."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Rubric:\n{rubric}\n\nTask:\n{prompt_body}",
                },
            ],
        )
        payload = json.loads(response.choices[0].message.content)
        score = max(1, min(5, int(payload["score"])))
        return {
            "score": score,
            "notes": str(payload.get("notes", "")).strip() or f"LLM judged {metric_name}.",
        }
    except Exception as e:
        return {
            "score": None,
            "notes": f"LLM-as-Judge error for {metric_name}: {e}",
        }


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def score_faithfulness(answer: str, chunks_used: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Faithfulness:
    Is the answer grounded in the retrieved context?
    """
    if answer.startswith("ERROR:") or answer == "PIPELINE_NOT_IMPLEMENTED":
        return {"score": 1, "notes": "Pipeline failed, so answer is not grounded."}

    if not chunks_used:
        return {"score": 1, "notes": "No retrieved chunks available to support the answer."}

    rubric = (
        "5 = every important claim in the answer is supported by the retrieved chunks.\n"
        "4 = almost fully grounded, only a very small unsupported detail.\n"
        "3 = mostly grounded, but includes some mild inference.\n"
        "2 = several important details are not in the context.\n"
        "1 = answer is mostly unsupported or hallucinates."
    )
    prompt_body = (
        f"Retrieved context:\n{_build_chunks_text(chunks_used)}\n\n"
        f"Answer to grade:\n{answer}\n\n"
        "Grade only whether the answer is supported by the provided context."
    )
    return _judge_score("faithfulness", rubric, prompt_body)


def score_answer_relevance(query: str, answer: str) -> Dict[str, Any]:
    """
    Answer Relevance:
    Does the answer directly address the query?
    """
    if answer.startswith("ERROR:") or answer == "PIPELINE_NOT_IMPLEMENTED":
        return {"score": 1, "notes": "Pipeline failed, so the answer does not address the query."}

    rubric = (
        "5 = directly answers the query and stays on target.\n"
        "4 = answers correctly but misses a minor point.\n"
        "3 = somewhat related but not fully on target.\n"
        "2 = partly off-topic.\n"
        "1 = does not answer the query."
    )
    prompt_body = (
        f"Query:\n{query}\n\n"
        f"Answer to grade:\n{answer}\n\n"
        "Grade only whether the answer actually addresses the user's question."
    )
    return _judge_score("answer_relevance", rubric, prompt_body)


def score_context_recall(chunks_used: List[Dict[str, Any]], expected_sources: List[str]) -> Dict[str, Any]:
    """
    Context Recall:
    Did retrieval bring back the expected evidence source(s)?
    """
    if not expected_sources:
        return {
            "score": None,
            "recall": None,
            "notes": "No expected sources (abstain or insufficient-context case).",
        }

    retrieved_sources = {
        c.get("metadata", {}).get("source", "")
        for c in chunks_used
    }

    found = 0
    missing = []
    for expected in expected_sources:
        expected_name = (
            expected.split("/")[-1]
            .replace(".pdf", "")
            .replace(".md", "")
            .replace(".txt", "")
        )
        matched = any(expected_name.lower() in src.lower() for src in retrieved_sources)
        if matched:
            found += 1
        else:
            missing.append(expected)

    recall = found / len(expected_sources)
    score = max(1, round(recall * 5))

    return {
        "score": score,
        "recall": recall,
        "found": found,
        "missing": missing,
        "notes": (
            f"Retrieved {found}/{len(expected_sources)} expected sources"
            + (f"; missing: {missing}" if missing else "")
        ),
    }


def score_completeness(query: str, answer: str, expected_answer: str) -> Dict[str, Any]:
    """
    Completeness:
    Does the answer cover the important points from the expected answer?
    """
    if answer.startswith("ERROR:") or answer == "PIPELINE_NOT_IMPLEMENTED":
        return {"score": 1, "notes": "Pipeline failed, so the answer cannot be complete."}

    rubric = (
        "5 = covers all important points from the expected answer.\n"
        "4 = misses one minor detail.\n"
        "3 = misses some important details but still captures the main idea.\n"
        "2 = misses many important details.\n"
        "1 = misses most of the core content."
    )
    prompt_body = (
        f"Query:\n{query}\n\n"
        f"Expected answer:\n{expected_answer}\n\n"
        f"Model answer to grade:\n{answer}\n\n"
        "Grade only how complete the model answer is compared with the expected answer."
    )
    return _judge_score("completeness", rubric, prompt_body)


# =============================================================================
# SCORECARD RUNNER
# =============================================================================

def run_scorecard(
    config: Dict[str, Any],
    test_questions: Optional[List[Dict[str, Any]]] = None,
    verbose: bool = True,
) -> List[Dict[str, Any]]:
    """
    Run all test questions through the pipeline and score each result.
    """
    if test_questions is None:
        with open(TEST_QUESTIONS_PATH, "r", encoding="utf-8") as f:
            test_questions = json.load(f)

    results = []
    label = config.get("label", "unnamed")

    print(f"\n{'=' * 70}")
    print(f"Running scorecard: {label}")
    print(f"Config: {config}")
    print("=" * 70)

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
            sources = result.get("sources", [])
        except NotImplementedError:
            answer = "PIPELINE_NOT_IMPLEMENTED"
            chunks_used = []
            sources = []
        except Exception as e:
            answer = f"ERROR: {e}"
            chunks_used = []
            sources = []

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
            "expected_sources": expected_sources,
            "retrieved_sources": list(sources),
            "chunks_retrieved": len(chunks_used),
            "faithfulness": faith["score"],
            "faithfulness_notes": faith["notes"],
            "relevance": relevance["score"],
            "relevance_notes": relevance["notes"],
            "context_recall": recall["score"],
            "context_recall_notes": recall["notes"],
            "completeness": complete["score"],
            "completeness_notes": complete["notes"],
            "config_label": label,
        }
        results.append(row)

        if verbose:
            preview = answer.replace("\n", " ")
            print(f"  Answer: {preview[:120]}...")
            print(
                f"  Faithful: {faith['score']} | Relevant: {relevance['score']} | "
                f"Recall: {recall['score']} | Complete: {complete['score']}"
            )

    for metric in ["faithfulness", "relevance", "context_recall", "completeness"]:
        scores = [r[metric] for r in results if r[metric] is not None]
        avg = sum(scores) / len(scores) if scores else None
        if avg is not None:
            print(f"\nAverage {metric}: {avg:.2f}")
        else:
            print(f"\nAverage {metric}: N/A")

    return results


# =============================================================================
# A/B COMPARISON
# =============================================================================

def compare_ab(
    baseline_results: List[Dict[str, Any]],
    variant_results: List[Dict[str, Any]],
    output_csv: Optional[str] = None,
) -> None:
    """
    Compare baseline vs variant overall and per question.
    """
    metrics = ["faithfulness", "relevance", "context_recall", "completeness"]

    print(f"\n{'=' * 70}")
    print("A/B Comparison: Baseline vs Variant")
    print("=" * 70)
    print(f"{'Metric':<20} {'Baseline':>10} {'Variant':>10} {'Delta':>8}")
    print("-" * 55)

    for metric in metrics:
        b_scores = [r[metric] for r in baseline_results if r[metric] is not None]
        v_scores = [r[metric] for r in variant_results if r[metric] is not None]

        b_avg = sum(b_scores) / len(b_scores) if b_scores else None
        v_avg = sum(v_scores) / len(v_scores) if v_scores else None
        delta = (v_avg - b_avg) if (b_avg is not None and v_avg is not None) else None

        b_str = f"{b_avg:.2f}" if b_avg is not None else "N/A"
        v_str = f"{v_avg:.2f}" if v_avg is not None else "N/A"
        d_str = f"{delta:+.2f}" if delta is not None else "N/A"

        print(f"{metric:<20} {b_str:>10} {v_str:>10} {d_str:>8}")

    print(f"\n{'QID':<6} {'Baseline F/R/Rc/C':<22} {'Variant F/R/Rc/C':<22} {'Better?':<10}")
    print("-" * 65)

    b_by_id = {r["id"]: r for r in baseline_results}
    for v_row in variant_results:
        qid = v_row["id"]
        b_row = b_by_id.get(qid, {})

        b_scores_str = "/".join(str(b_row.get(m, "?")) for m in metrics)
        v_scores_str = "/".join(str(v_row.get(m, "?")) for m in metrics)

        b_total = sum((b_row.get(m, 0) or 0) for m in metrics)
        v_total = sum((v_row.get(m, 0) or 0) for m in metrics)
        better = "Variant" if v_total > b_total else ("Baseline" if b_total > v_total else "Tie")

        print(f"{qid:<6} {b_scores_str:<22} {v_scores_str:<22} {better:<10}")

    if output_csv:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = RESULTS_DIR / output_csv
        combined = baseline_results + variant_results
        if combined:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=combined[0].keys())
                writer.writeheader()
                writer.writerows(combined)
            print(f"\nSaved A/B comparison rows to: {csv_path}")


# =============================================================================
# GRADING LOG
# =============================================================================

def generate_grading_log(
    config: Dict[str, Any],
    grading_questions_path: Path = GRADING_QUESTIONS_PATH,
    output_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Create logs/grading_run.json with the format required by SCORING.md.
    """
    if output_path is None:
        output_path = LOGS_DIR / "grading_run.json"

    with open(grading_questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    rows = []
    for q in questions:
        try:
            result = rag_answer(
                query=q["question"],
                retrieval_mode=config.get("retrieval_mode", "dense"),
                top_k_search=config.get("top_k_search", 10),
                top_k_select=config.get("top_k_select", 3),
                use_rerank=config.get("use_rerank", False),
                verbose=False,
            )
            answer = result["answer"]
            sources = result["sources"]
            chunks_retrieved = len(result["chunks_used"])
            retrieval_mode = result["config"]["retrieval_mode"]
        except Exception as e:
            answer = f"PIPELINE_ERROR: {e}"
            sources = []
            chunks_retrieved = 0
            retrieval_mode = config.get("retrieval_mode", "dense")

        rows.append({
            "id": q["id"],
            "question": q["question"],
            "answer": answer,
            "sources": sources,
            "chunks_retrieved": chunks_retrieved,
            "retrieval_mode": retrieval_mode,
            "timestamp": datetime.now().isoformat(),
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


# =============================================================================
# REPORT GENERATOR
# =============================================================================

def generate_scorecard_summary(results: List[Dict[str, Any]], label: str) -> str:
    """
    Create a markdown scorecard summary.
    """
    metrics = ["faithfulness", "relevance", "context_recall", "completeness"]
    averages = {}
    for metric in metrics:
        scores = [r[metric] for r in results if r[metric] is not None]
        averages[metric] = sum(scores) / len(scores) if scores else None

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = f"""# Scorecard: {label}
Generated: {timestamp}

## Summary

| Metric | Average Score |
|--------|---------------|
"""
    for metric, avg in averages.items():
        avg_str = f"{avg:.2f}/5" if avg is not None else "N/A"
        md += f"| {metric.replace('_', ' ').title()} | {avg_str} |\n"

    md += "\n## Per-Question Results\n\n"
    md += "| ID | Category | Faithful | Relevant | Recall | Complete | Notes |\n"
    md += "|----|----------|----------|----------|--------|----------|-------|\n"

    for r in results:
        notes = r.get("faithfulness_notes", "")[:50]
        md += (
            f"| {r['id']} | {r['category']} | {r.get('faithfulness', 'N/A')} | "
            f"{r.get('relevance', 'N/A')} | {r.get('context_recall', 'N/A')} | "
            f"{r.get('completeness', 'N/A')} | {notes} |\n"
        )

    return md


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 4: Evaluation & Scorecard")
    print("=" * 60)

    print(f"\nLoading test questions from: {TEST_QUESTIONS_PATH}")
    try:
        with open(TEST_QUESTIONS_PATH, "r", encoding="utf-8") as f:
            test_questions = json.load(f)
        print(f"Found {len(test_questions)} test questions")
        for q in test_questions[:3]:
            print(f"  [{q['id']}] {q['question']} ({q['category']})")
        print("  ...")
    except FileNotFoundError:
        print("Could not find test_questions.json")
        test_questions = []

    print("\n--- Running Baseline ---")
    try:
        baseline_results = run_scorecard(
            config=BASELINE_CONFIG,
            test_questions=test_questions,
            verbose=True,
        )
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        baseline_md = generate_scorecard_summary(baseline_results, BASELINE_CONFIG["label"])
        baseline_path = RESULTS_DIR / "scorecard_baseline.md"
        baseline_path.write_text(baseline_md, encoding="utf-8")
        print(f"\nSaved baseline scorecard to: {baseline_path}")
    except Exception as e:
        print(f"Could not run baseline: {e}")
        baseline_results = []

    print("\n--- Running Variant ---")
    try:
        variant_results = run_scorecard(
            config=VARIANT_CONFIG,
            test_questions=test_questions,
            verbose=True,
        )
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        variant_md = generate_scorecard_summary(variant_results, VARIANT_CONFIG["label"])
        variant_path = RESULTS_DIR / "scorecard_variant.md"
        variant_path.write_text(variant_md, encoding="utf-8")
        print(f"Saved variant scorecard to: {variant_path}")
    except Exception as e:
        print(f"Could not run variant: {e}")
        variant_results = []

    if baseline_results and variant_results:
        compare_ab(
            baseline_results,
            variant_results,
            output_csv="ab_comparison.csv",
        )

    if GRADING_QUESTIONS_PATH.exists():
        print("\n--- Generating Grading Log ---")
        try:
            rows = generate_grading_log(VARIANT_CONFIG, GRADING_QUESTIONS_PATH)
            print(f"Saved {len(rows)} grading rows to: {LOGS_DIR / 'grading_run.json'}")
        except Exception as e:
            print(f"Could not generate grading log: {e}")

    print("\nSprint 4 evaluation complete.")
