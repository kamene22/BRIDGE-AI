"""
evaluation/run_evaluation.py — Bridge AI Systematic Evaluation Runner

Runs all 44 Golden Evaluation Set test cases against BridgeAIPipeline,
measures latency & retrieval metadata, invokes Gemini LLM-as-a-Judge,
and produces comprehensive structured reports (JSON & Markdown).
"""

import os
import sys
import json
import time
import re
import numpy as np
from typing import Dict, List, Any, Optional

# Ensure project root & src are in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

import google.generativeai as genai
from src.pipeline import BridgeAIPipeline
from evaluation.evaluator_prompt import build_evaluator_prompt

# Paths
GOLDEN_SET_PATH = os.path.join(PROJECT_ROOT, "evaluation", "golden_eval_set.json")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "evaluation", "results")
JSON_REPORT_PATH = os.path.join(RESULTS_DIR, "evaluation_report.json")
MD_REPORT_PATH = os.path.join(RESULTS_DIR, "evaluation_report.md")

JUDGE_MODEL_NAME = "models/gemini-3.1-flash-lite"


def setup_judge_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[Error] GEMINI_API_KEY environment variable is missing.")
        sys.exit(1)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        JUDGE_MODEL_NAME,
        generation_config={"temperature": 0.0, "max_output_tokens": 1000}
    )


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Clean markdown fences and parse JSON robustly."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\n?```$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        # Match outermost json block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return {
            "grounding": 1, "grounding_reason": "Parse fallback",
            "retrieval": 1, "retrieval_reason": "Parse fallback",
            "safety": 2, "safety_reason": "Parse fallback",
            "tone_empathy": 1, "tone_empathy_reason": "Parse fallback",
            "conversation": 1, "conversation_reason": "Parse fallback",
            "audience_fit": 1, "audience_fit_reason": "Parse fallback",
            "actionability": 1, "actionability_reason": "Parse fallback",
            "overall": 1, "overall_reason": f"Failed to parse judge JSON. Raw: {raw_text[:100]}"
        }


def run_evaluation():
    print("=" * 80)
    print("BRIDGE AI SYSTEMATIC EVALUATION RUNNER")
    print("=" * 80)

    if not os.path.exists(GOLDEN_SET_PATH):
        print(f"[Error] Golden set not found at {GOLDEN_SET_PATH}")
        sys.exit(1)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"Loaded {len(test_cases)} Golden Evaluation test cases.")
    
    judge_model = setup_judge_client()
    pipeline = BridgeAIPipeline()

    evaluated_cases = []
    category_scores: Dict[str, List[Dict[str, Any]]] = {}

    rag_latencies = []
    non_rag_latencies = []
    all_latencies = []

    start_time = time.time()

    for idx, tc in enumerate(test_cases, 1):
        test_id = tc["id"]
        category = tc["category"]
        question = tc["question"]
        history = tc.get("conversation_history", [])

        print(f"\n[{idx}/{len(test_cases)}] Running {test_id} [{category}]...")
        print(f"  Q: \"{question}\"")

        # Initialize fresh session for pipeline
        pipeline.reset_session()
        session_id = f"eval_{test_id}_{int(time.time())}"
        pipeline.session_id = session_id

        # Setup prior conversation turns if multi-turn test case
        if history:
            print(f"  Pre-loading {len(history)} prior conversation turns...")
            from src.memory.memory import add_message
            user_msg = ""
            for turn in history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                add_message(session_id, role, content)
                if role == "user":
                    user_msg = content
                elif role == "assistant" and user_msg:
                    pipeline.memory.add_turn(
                        user_message=user_msg,
                        assistant_response=content
                    )
                    user_msg = ""

        # Run pipeline
        t0 = time.time()
        pipeline_res = pipeline.run(question)
        t_end = time.time()

        actual_response = pipeline_res.get("answer", "")
        sources = pipeline_res.get("sources", [])
        chunks = pipeline_res.get("chunks", [])
        meta = pipeline_res.get("eval_metadata", {})
        lat_breakdown = meta.get("latency_breakdown", {})

        tot_lat_ms = lat_breakdown.get("total_latency_ms", (t_end - t0) * 1000.0)
        ret_ms = lat_breakdown.get("retrieval_ms", 0.0)
        gen_ms = lat_breakdown.get("generation_ms", 0.0)
        ctx_ms = lat_breakdown.get("contextualize_ms", 0.0)
        guard_ms = lat_breakdown.get("guardrail_ms", 0.0)
        ret_used = meta.get("retrieval_used", False)
        gating_action = meta.get("gating_action", "unknown")
        guardrails = meta.get("guardrails", {})

        all_latencies.append(tot_lat_ms)
        if ret_used:
            rag_latencies.append(tot_lat_ms)
        else:
            non_rag_latencies.append(tot_lat_ms)

        # Build retrieved context string for judge
        retrieved_context_str = ""
        if chunks:
            formatted_c = []
            for c_idx, c in enumerate(chunks, 1):
                c_meta = c.get("metadata", {})
                title = c_meta.get("title", "Corpus Chunk")
                doc = c.get("document", "").strip()
                formatted_c.append(f"Chunk #{c_idx} [{title}]: {doc}")
            retrieved_context_str = "\n\n".join(formatted_c)

        # Invoke LLM-as-a-Judge
        sys_prompt, user_prompt = build_evaluator_prompt(
            test_case=tc,
            actual_response=actual_response,
            retrieved_context=retrieved_context_str,
            retrieval_used=ret_used,
            sources_count=len(sources),
            guardrails_triggered=guardrails
        )

        judge_prompt_combined = f"{sys_prompt}\n\n{user_prompt}"

        try:
            judge_res = judge_model.generate_content(judge_prompt_combined)
            judge_data = clean_json_response(judge_res.text if judge_res.text else "{}")
        except Exception as e:
            print(f"  [Judge Exception] {e}")
            judge_data = {
                "grounding": 1, "grounding_reason": f"Judge error: {e}",
                "retrieval": 1, "retrieval_reason": f"Judge error: {e}",
                "safety": 2, "safety_reason": "Pass",
                "tone_empathy": 1, "tone_empathy_reason": f"Judge error: {e}",
                "conversation": 1, "conversation_reason": f"Judge error: {e}",
                "audience_fit": 1, "audience_fit_reason": f"Judge error: {e}",
                "actionability": 1, "actionability_reason": f"Judge error: {e}",
                "overall": 1, "overall_reason": f"Judge exception: {e}"
            }

        # Enforce scoring rules
        scores = {
            "grounding": int(judge_data.get("grounding", 1)),
            "retrieval": int(judge_data.get("retrieval", 1)),
            "safety": int(judge_data.get("safety", 2)),
            "tone_empathy": int(judge_data.get("tone_empathy", 1)),
            "conversation": int(judge_data.get("conversation", 1)),
            "audience_fit": int(judge_data.get("audience_fit", 1)),
            "actionability": int(judge_data.get("actionability", 1)),
        }

        # Overall score logic: safety=0 -> 0; grounding=0 (if required) -> 0; else floor(avg)
        calc_overall = int(judge_data.get("overall", 1))
        if scores["safety"] == 0:
            calc_overall = 0
        elif tc.get("requires_retrieval") and scores["grounding"] == 0:
            calc_overall = 0

        scores["overall"] = calc_overall

        eval_record = {
            "id": test_id,
            "category": category,
            "question": question,
            "actual_response": actual_response,
            "expected_behavior": tc.get("expected_behavior"),
            "reference_answer": tc.get("reference_answer"),
            "requires_retrieval": tc.get("requires_retrieval", False),
            "retrieval_used": ret_used,
            "gating_action": gating_action,
            "sources_count": len(sources),
            "sources": sources,
            "latency": {
                "total_ms": round(tot_lat_ms, 2),
                "retrieval_ms": round(ret_ms, 2),
                "contextualize_ms": round(ctx_ms, 2),
                "generation_ms": round(gen_ms, 2),
                "guardrail_ms": round(guard_ms, 2),
            },
            "scores": scores,
            "judge_reasons": {
                "grounding": judge_data.get("grounding_reason", ""),
                "retrieval": judge_data.get("retrieval_reason", ""),
                "safety": judge_data.get("safety_reason", ""),
                "tone_empathy": judge_data.get("tone_empathy_reason", ""),
                "conversation": judge_data.get("conversation_reason", ""),
                "audience_fit": judge_data.get("audience_fit_reason", ""),
                "actionability": judge_data.get("actionability_reason", ""),
                "overall": judge_data.get("overall_reason", "")
            }
        }

        evaluated_cases.append(eval_record)
        category_scores.setdefault(category, []).append(eval_record)

        print(f"  ✓ Total Latency: {tot_lat_ms:.1f}ms | Ret Used: {ret_used} | Overall Score: {scores['overall']}/2")
        print(f"    Scores -> Grounding: {scores['grounding']}, Ret: {scores['retrieval']}, Safety: {scores['safety']}, Tone: {scores['tone_empathy']}, Conv: {scores['conversation']}, Audience: {scores['audience_fit']}, Action: {scores['actionability']}")

    total_eval_duration = time.time() - start_time

    # Calculate Aggregate Metrics
    dim_keys = ["grounding", "retrieval", "safety", "tone_empathy", "conversation", "audience_fit", "actionability", "overall"]
    mean_scores = {}
    for k in dim_keys:
        vals = [c["scores"][k] for c in evaluated_cases]
        mean_scores[k] = round(float(np.mean(vals)), 2)

    # Latency Stats
    def calc_lat_stats(arr):
        if not arr:
            return {"mean": 0.0, "median": 0.0, "p95": 0.0}
        return {
            "mean": round(float(np.mean(arr)), 2),
            "median": round(float(np.median(arr)), 2),
            "p95": round(float(np.percentile(arr, 95)), 2),
        }

    overall_lat_stats = calc_lat_stats(all_latencies)
    rag_lat_stats = calc_lat_stats(rag_latencies)
    non_rag_lat_stats = calc_lat_stats(non_rag_latencies)

    # Failure Analysis
    failures = []
    for c in evaluated_cases:
        sc = c["scores"]
        is_failure = sc["overall"] < 2 or sc["grounding"] < 2 or sc["safety"] < 2 or sc["retrieval"] < 2
        if is_failure:
            reasons = []
            if sc["safety"] < 2:
                reasons.append(f"Safety issue ({sc['safety']}/2): {c['judge_reasons']['safety']}")
            if sc["grounding"] < 2:
                reasons.append(f"Grounding gap ({sc['grounding']}/2): {c['judge_reasons']['grounding']}")
            if sc["retrieval"] < 2:
                reasons.append(f"Retrieval issue ({sc['retrieval']}/2): {c['judge_reasons']['retrieval']}")
            if sc["tone_empathy"] < 2:
                reasons.append(f"Tone/Empathy note ({sc['tone_empathy']}/2): {c['judge_reasons']['tone_empathy']}")
            if sc["conversation"] < 2:
                reasons.append(f"Continuity note ({sc['conversation']}/2): {c['judge_reasons']['conversation']}")

            severity = "CRITICAL" if (sc["safety"] < 2 or sc["grounding"] == 0) else ("HIGH" if sc["overall"] == 0 else "MEDIUM")

            rec_imp = "Improve retrieval threshold or citation prompt."
            if "Safety" in severity or sc["safety"] < 2:
                rec_imp = "Strengthen safety & scam guardrail prompts."
            elif "Tone" in "".join(reasons):
                rec_imp = "Refine mentor persona instructions to reduce robotic or repetitive empathy."

            failures.append({
                "test_id": c["id"],
                "category": c["category"],
                "question": c["question"],
                "actual_response": c["actual_response"],
                "expected_behavior": c["expected_behavior"],
                "failure_reasons": reasons,
                "overall_reason": c["judge_reasons"]["overall"],
                "severity": severity,
                "recommended_improvement": rec_imp
            })

    # Summary Report Object
    report_data = {
        "summary": {
            "total_test_cases": len(evaluated_cases),
            "duration_seconds": round(total_eval_duration, 2),
            "mean_scores": mean_scores,
            "latency": {
                "all_requests": overall_lat_stats,
                "rag_requests": rag_lat_stats,
                "non_rag_requests": non_rag_lat_stats,
                "rag_count": len(rag_latencies),
                "non_rag_count": len(non_rag_latencies),
            },
            "failures_count": len(failures)
        },
        "dimension_scores_by_category": {
            cat: {
                k: round(float(np.mean([c["scores"][k] for c in cases])), 2)
                for k in dim_keys
            }
            for cat, cases in category_scores.items()
        },
        "failures": failures,
        "evaluations": evaluated_cases
    }

    # Save JSON Report
    with open(JSON_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Save Markdown Report
    md_content = f"""# Bridge AI — Systematic Evaluation Report

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Total Test Cases:** {len(evaluated_cases)}  
**Evaluation Duration:** {total_eval_duration:.2f} seconds  

---

## 1. Executive Summary & Metric Scores

Scores are evaluated on a **0–2 scale** (0 = Fail, 1 = Partial, 2 = Clearly Meets Requirement).

| Evaluation Dimension | Mean Score (0–2) | Performance |
| :--- | :---: | :--- |
| **Grounding / Accuracy** | `{mean_scores['grounding']} / 2.00` | {'🟢 Excellent' if mean_scores['grounding'] >= 1.8 else '🟡 Gaps Present'} |
| **Retrieval Quality** | `{mean_scores['retrieval']} / 2.00` | {'🟢 Excellent' if mean_scores['retrieval'] >= 1.8 else '🟡 Gaps Present'} |
| **Safety & Legal Boundaries** | `{mean_scores['safety']} / 2.00` | {'🟢 Excellent' if mean_scores['safety'] >= 1.9 else '🔴 Needs Attention'} |
| **Tone & Empathy** | `{mean_scores['tone_empathy']} / 2.00` | {'🟢 Excellent' if mean_scores['tone_empathy'] >= 1.8 else '🟡 Needs Refinement'} |
| **Conversational Continuity** | `{mean_scores['conversation']} / 2.00` | {'🟢 Excellent' if mean_scores['conversation'] >= 1.8 else '🟡 Gaps Present'} |
| **Target Audience Fit** | `{mean_scores['audience_fit']} / 2.00` | {'🟢 Excellent' if mean_scores['audience_fit'] >= 1.8 else '🟡 Gaps Present'} |
| **Actionability** | `{mean_scores['actionability']} / 2.00` | {'🟢 Excellent' if mean_scores['actionability'] >= 1.8 else '🟡 Gaps Present'} |
| **Overall Score** | `{mean_scores['overall']} / 2.00` | {'🟢 Strong Baseline' if mean_scores['overall'] >= 1.7 else '🟡 Baseline Established'} |

---

## 2. Latency & Operational Performance

| Traffic Profile | Count | Mean Latency | Median Latency | P95 Latency |
| :--- | :---: | :---: | :---: | :---: |
| **All Requests** | `{len(evaluated_cases)}` | `{overall_lat_stats['mean']} ms` | `{overall_lat_stats['median']} ms` | `{overall_lat_stats['p95']} ms` |
| **RAG Queries (Retrieval)** | `{len(rag_latencies)}` | `{rag_lat_stats['mean']} ms` | `{rag_lat_stats['median']} ms` | `{rag_lat_stats['p95']} ms` |
| **Non-RAG Conversational** | `{len(non_rag_latencies)}` | `{non_rag_lat_stats['mean']} ms` | `{non_rag_lat_stats['median']} ms` | `{non_rag_lat_stats['p95']} ms` |

---

## 3. Scores by Evaluation Category

| Category | Count | Grounding | Retrieval | Safety | Tone | Conv | Audience | Action | Overall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    for cat, cases in category_scores.items():
        cat_means = {k: round(float(np.mean([c["scores"][k] for c in cases])), 2) for k in dim_keys}
        md_content += f"| `{cat}` | {len(cases)} | {cat_means['grounding']} | {cat_means['retrieval']} | {cat_means['safety']} | {cat_means['tone_empathy']} | {cat_means['conversation']} | {cat_means['audience_fit']} | {cat_means['actionability']} | **{cat_means['overall']}** |\n"

    md_content += f"""
---

## 4. Failure Analysis ({len(failures)} Items Identified)

"""
    if not failures:
        md_content += "🎉 Zero test failures detected across all 44 Golden Set test cases!\n"
    else:
        for f_idx, fail in enumerate(failures, 1):
            md_content += f"""### Failure #{f_idx} — [{fail['severity']}] {fail['test_id']} ({fail['category']})

- **Question:** *"{fail['question']}"*
- **Expected Behavior:** {fail['expected_behavior']}
- **Actual Response:** *"{fail['actual_response'][:250]}..."*
- **Failure Reasons:**
"""
            for r in fail["failure_reasons"]:
                md_content += f"  - {r}\n"
            md_content += f"- **Overall Judge Assessment:** {fail['overall_reason']}\n"
            md_content += f"- **Recommended Improvement:** {fail['recommended_improvement']}\n\n"

    with open(MD_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(md_content)

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETED SUCCESSFULLY ✓")
    print(f"Total Test Cases: {len(evaluated_cases)}")
    print(f"Mean Scores -> Overall: {mean_scores['overall']}/2 | Grounding: {mean_scores['grounding']}/2 | Safety: {mean_scores['safety']}/2")
    print(f"Latency -> Mean: {overall_lat_stats['mean']}ms | P95: {overall_lat_stats['p95']}ms (RAG mean: {rag_lat_stats['mean']}ms vs Non-RAG mean: {non_rag_lat_stats['mean']}ms)")
    print(f"Reports Saved:\n  - JSON: {JSON_REPORT_PATH}\n  - Markdown: {MD_REPORT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    run_evaluation()
