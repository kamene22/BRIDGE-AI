"""
evaluation/run_10_turn_first_job_journey.py — 10-Turn First Job Journey Simulation
Simulates a real early-career graduate landing their first job in Kenya.
Records exact transcript ("what was said") and latency breakdown per turn.
"""

import os
import sys
import time
import json
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.pipeline import BridgeAIPipeline

FIRST_JOB_TURNS = [
    "Ahh, I just landed my first job as a Junior Communications Assistant at an NGO in Upper Hill! I'm so excited but really nervous!",
    "What should I prepare or wear for my very first day?",
    "My offer letter says my probation is 6 months. Is that normal in Kenya?",
    "Can my employer extend probation beyond 6 months?",
    "What statutory deductions should I expect on my first payslip?",
    "What if someone asks me to send KES 2,000 via M-Pesa for a staff badge or uniform fee?",
    "I accidentally sent an internal draft email to the wrong person at work 😭 what should I do?",
    "My manager barely speaks to me during my first week. Does she dislike me?",
    "How many days of paid annual leave am I entitled to under the Kenya Employment Act?",
    "Okay, thank you so much Amani! That helps me feel so much more confident."
]

def run_10_turn_test():
    session_id = f"first_job_{uuid.uuid4().hex[:6]}"
    pipeline = BridgeAIPipeline(session_id=session_id)

    report_data = []

    print("=" * 90)
    print("RUNNING 10-TURN FIRST JOB JOURNEY BENCHMARK TEST")
    print("=" * 90)

    total_latency_sum = 0.0

    for i, user_msg in enumerate(FIRST_JOB_TURNS, 1):
        print(f"\n[Turn {i}/10] User: \"{user_msg}\"")
        t_start = time.perf_counter()
        
        # Execute query turn
        res = pipeline.run(user_msg)
        t_end = time.perf_counter()

        tot_ms = (t_end - t_start) * 1000.0
        total_latency_sum += tot_ms

        ans = res.get("answer", "")
        sources = res.get("sources", [])
        meta = res.get("eval_metadata", {})
        lat_bd = meta.get("latency_breakdown", {})

        print(f"  ├─ Latency        : {tot_ms:.2f} ms")
        print(f"  ├─ Retrieval Gating: {meta.get('route_name', 'conversational')}")
        print(f"  ├─ Vector Search  : {lat_bd.get('retrieval_ms', 0):.2f} ms")
        print(f"  ├─ Generation     : {lat_bd.get('generation_ms', 0):.2f} ms")
        print(f"  ├─ Sources        : {len(sources)} cited")
        print(f"  └─ Amani Said     :\n{ans}\n")

        report_data.append({
            "turn_number": i,
            "user_message": user_msg,
            "amani_response": ans,
            "sources_cited": sources,
            "route_name": meta.get("route_name", "conversational"),
            "retrieval_used": meta.get("retrieval_used", False),
            "latency_breakdown": {
                "intent_ms": lat_bd.get("intent_ms", 0),
                "retrieval_gating_ms": lat_bd.get("retrieval_gating_ms", 0),
                "retrieval_ms": lat_bd.get("retrieval_ms", 0),
                "generation_ms": lat_bd.get("generation_ms", 0),
                "total_latency_ms": round(tot_ms, 2)
            }
        })

    avg_latency = total_latency_sum / len(FIRST_JOB_TURNS)

    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "first_job_10_turn_report.json"))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total_turns": 10,
                "average_turn_latency_ms": round(avg_latency, 2),
                "total_journey_duration_sec": round(total_latency_sum / 1000.0, 2)
            },
            "turns": report_data
        }, f, indent=2)

    print("=" * 90)
    print(f"10-TURN TEST COMPLETED — Average Turn Latency: {avg_latency:.2f} ms")
    print(f"Detailed report saved to {output_path}")
    print("=" * 90)

if __name__ == "__main__":
    run_10_turn_test()
