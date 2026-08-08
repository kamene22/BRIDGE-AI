"""
src/api/server.py — FastAPI Backend Server for Bridge AI (Amani)

Exposes REST API endpoints for:
  - GET  /api/welcome    : Returns initial mentor greeting.
  - POST /api/chat       : Executes the full RAG & hybrid reasoning pipeline.
  - GET  /api/telemetry  : Returns server usage metrics.
  - POST /api/reset      : Clears conversation memory for a session.
"""

import os
import sys
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline import BridgeAIPipeline

app = FastAPI(
    title="Bridge AI (Amani) Backend API",
    description="Multimodal Grounded RAG & Hybrid Reasoning Mentor for Young Kenyans",
    version="1.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session pipelines store (in-memory per session_id)
session_pipelines: Dict[str, BridgeAIPipeline] = {}
default_pipeline = BridgeAIPipeline()

# Telemetry metrics
metrics = {
    "total_requests": 0,
    "total_latency_ms": 0,
    "scam_flags": 0,
    "out_of_scope_flags": 0,
    "legal_disclaimers": 0,
}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    redirected: bool
    guardrails: Dict[str, bool]
    latency_ms: int
    intent: str


def get_pipeline(session_id: str) -> BridgeAIPipeline:
    if session_id not in session_pipelines:
        session_pipelines[session_id] = BridgeAIPipeline()
    return session_pipelines[session_id]


@app.get("/api/welcome")
def welcome():
    return {
        "message": (
            "Hujambo! I'm Bridge AI (Amani), your career mentor. "
            "Whether you're looking for your first job, navigating probation, "
            "or spotting scam job offers in Kenya, I'm here to help."
        )
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    t0 = time.time()
    pipe = get_pipeline(req.session_id)
    
    # Fast path for simple greetings to optimize latency (<50ms)
    clean_msg = req.message.strip().lower()
    if clean_msg in ["hello", "hi", "hey", "hujambo", "habari", "good morning", "good afternoon"]:
        lat = int((time.time() - t0) * 1000)
        metrics["total_requests"] += 1
        metrics["total_latency_ms"] += lat
        return ChatResponse(
            answer="Hujambo! How can I support your career journey in Kenya today? Feel free to ask about applications, interviews, probation rights, or verifying job offers.",
            sources=[],
            redirected=False,
            guardrails={"scam_detected": False, "legal_boundary_triggered": False, "out_of_scope": False},
            latency_ms=lat,
            intent="Greeting"
        )

    res = pipe.run(req.message)
    lat = int((time.time() - t0) * 1000)

    # Update telemetry metrics
    metrics["total_requests"] += 1
    metrics["total_latency_ms"] += lat
    if res["trace"]["guardrails"]["scam_detected"]:
        metrics["scam_flags"] += 1
    if res["trace"]["guardrails"]["out_of_scope"]:
        metrics["out_of_scope_flags"] += 1
    if res["trace"]["guardrails"]["legal_boundary_triggered"]:
        metrics["legal_disclaimers"] += 1

    return ChatResponse(
        answer=res["answer"],
        sources=res["sources"],
        redirected=res["trace"]["guardrails"]["out_of_scope"],
        guardrails=res["trace"]["guardrails"],
        latency_ms=lat,
        intent=res["trace"].get("intent", {}).get("intent", "General")
    )


@app.get("/api/telemetry")
def get_telemetry():
    avg_latency = (
        metrics["total_latency_ms"] / metrics["total_requests"]
        if metrics["total_requests"] > 0
        else 0
    )
    return {
        "total_requests": metrics["total_requests"],
        "average_latency_ms": round(avg_latency, 2),
        "scam_flags_detected": metrics["scam_flags"],
        "out_of_scope_redirects": metrics["out_of_scope_flags"],
        "legal_disclaimers_added": metrics["legal_disclaimers"],
        "active_sessions": len(session_pipelines)
    }


@app.post("/api/reset")
def reset_session(session_id: str = "default"):
    if session_id in session_pipelines:
        session_pipelines[session_id] = BridgeAIPipeline()
    return {"status": "success", "message": f"Session '{session_id}' reset successfully."}
