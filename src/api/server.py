import os
import sys
import time
import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    import google.generativeai as genai

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline import BridgeAIPipeline

app = FastAPI(
    title='Bridge AI (Amani) Backend API',
    description='Multimodal Grounded RAG Hybrid Reasoning Mentor for Young Kenyans',
    version='1.0.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

session_pipelines: Dict[str, BridgeAIPipeline] = {}

def get_pipeline(session_id: str) -> BridgeAIPipeline:
    if session_id not in session_pipelines:
        session_pipelines[session_id] = BridgeAIPipeline(session_id=session_id)
    return session_pipelines[session_id]

metrics = {
    'total_requests': 0,
    'total_latency_ms': 0,
    'scam_flags': 0,
    'out_of_scope_flags': 0,
    'legal_disclaimers': 0,
}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = 'default'

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "What are my legal rights during probation in Kenya?",
                    "session_id": "demo_session"
                }
            ]
        }
    }

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    redirected: bool
    guardrails: Dict[str, bool]
    latency_ms: int
    intent: str
    eval_metadata: Optional[Dict[str, Any]] = None

class VoiceToolRequest(BaseModel):
    function_name: str
    arguments: Dict[str, Any]
    session_id: Optional[str] = 'default'

@app.get('/')
def root():
    return {
        'status': 'online',
        'app': 'Bridge AI (Amani) Backend API',
        'version': '1.0.0',
        'docs_url': '/docs',
        'health_url': '/health'
    }

@app.get('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.datetime.now(tz=datetime.timezone.utc).isoformat()}

@app.get('/api/welcome')
def welcome():
    return {
        'message': (
            'Hujambo! I am Amani. How can I support your career journey in Kenya today? '
            'Feel free to ask about applications, interviews, probation rights, or verifying job offers'
        )
    }

@app.post('/api/session')
def new_session():
    from memory.memory import create_session
    sid = create_session()
    session_pipelines[sid] = BridgeAIPipeline(session_id=sid)
    return {'session_id': sid, 'status': 'initialized'}

@app.post('/api/token')
def get_ephemeral_token():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='GEMINI_API_KEY not configured on backend.')
    try:
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        expire_time = now + datetime.timedelta(minutes=30)
        
        token = client.auth_tokens.create(
            config={
                'uses': 1,
                'expire_time': expire_time.isoformat(),
                'new_session_expire_time': (now + datetime.timedelta(minutes=1)).isoformat(),
                'http_options': {'api_version': 'v1alpha'},
            }
        )
        return {
            'token': token.name,
            'expires_at': expire_time.isoformat()
        }
    except Exception as e:
        print(f'Error generating ephemeral token: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/voice-rag')
def voice_rag(req: VoiceToolRequest):
    t0 = time.time()
    pipe = get_pipeline(req.session_id)
    query = req.arguments.get('query', '')
    if not query:
        return {
            'answer': 'No search query provided.',
            'sources': [],
            'guardrails': {'scam_detected': False, 'legal_boundary_triggered': False, 'out_of_scope': False}
        }

    clean_q = query.strip().lower()
    is_oos = any(kw in clean_q for kw in ['crypto', 'bitcoin', 'sports betting', 'aviator', 'weather forecast', 'capital of france'])
    scam_detected = any(kw in clean_q for kw in ['mpesa paybill', 'registration fee', 'interview fee', 'medical fee'])
    legal_triggered = any(kw in clean_q for kw in ['cannot legally', 'is illegal under', 'you are legally entitled', 'sue them in', 'probation rights', 'contract', 'section 42', 'employment act'])

    if is_oos:
        return {
            'answer': 'That is outside what Bridge AI is built to help with. I focus on Kenyan employment, career guidance, and job verification.',
            'sources': [],
            'guardrails': {'out_of_scope': True, 'scam_detected': False, 'legal_boundary_triggered': False}
        }

    chunks = pipe.retriever.retrieve(query, top_k=3, distance_threshold=0.75)
    
    sources = []
    formatted_chunks = []
    for idx, c in enumerate(chunks, 1):
        meta = c.get('metadata', {})
        title = meta.get('title', 'Employment Guide')
        s_line = meta.get('start_line', '?')
        e_line = meta.get('end_line', '?')
        c_idx = meta.get('chunk_index', '?')
        loc = f'Lines {s_line}-{e_line}' if 'start_line' in meta else f'Chunk {c_idx}'
        source_str = f'{title} ({loc})'
        sources.append(source_str)
        content = c.get('content', '').strip()
        formatted_chunks.append(f'{idx}. [{source_str}]: {content}')

    if formatted_chunks:
        answer_text = 'GROUNDED KNOWLEDGE BASE RESULTS:\n\n' + '\n\n'.join(formatted_chunks)
    else:
        answer_text = 'No direct knowledge base documents found. Use general Kenyan career mentorship guidance.'

    lat = int((time.time() - t0) * 1000)
    
    metrics['total_requests'] += 1
    metrics['total_latency_ms'] += lat
    if scam_detected: metrics['scam_flags'] += 1
    if legal_triggered: metrics['legal_disclaimers'] += 1

    return {
        'answer': answer_text,
        'sources': sources,
        'guardrails': {
            'scam_detected': scam_detected,
            'legal_boundary_triggered': legal_triggered,
            'out_of_scope': False
        },
        'latency_ms': lat
    }

@app.post('/api/chat', response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail='Message cannot be empty.')

    try:
        t0 = time.time()
        pipe = get_pipeline(req.session_id)

        res = pipe.conversational_rag_query(req.message, session_id=req.session_id)
        lat = int((time.time() - t0) * 1000)

        metrics['total_requests'] += 1
        metrics['total_latency_ms'] += lat
        g_trace = res.get('trace', {}).get('guardrails', {})
        if g_trace.get('scam_detected'):
            metrics['scam_flags'] += 1
        if g_trace.get('out_of_scope'):
            metrics['out_of_scope_flags'] += 1
        if g_trace.get('legal_boundary_triggered'):
            metrics['legal_disclaimers'] += 1

        return ChatResponse(
            answer=res['answer'],
            sources=res['sources'],
            redirected=res.get('redirected', False),
            guardrails=g_trace,
            latency_ms=lat,
            intent=res.get('trace', {}).get('intent', {}).get('intent', 'General'),
            eval_metadata=res.get('eval_metadata')
        )
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/telemetry')
def get_telemetry():
    avg_latency = (
        metrics['total_latency_ms'] / metrics['total_requests']
        if metrics['total_requests'] > 0
        else 0
    )
    return {
        'total_requests': metrics['total_requests'],
        'average_latency_ms': round(avg_latency, 2),
        'scam_flags_detected': metrics['scam_flags'],
        'out_of_scope_redirects': metrics['out_of_scope_flags'],
        'legal_disclaimers_added': metrics['legal_disclaimers'],
        'active_sessions': len(session_pipelines)
    }

@app.post('/api/reset')
def reset_session(session_id: str = 'default'):
    if session_id in session_pipelines:
        session_pipelines[session_id] = BridgeAIPipeline(session_id=session_id)
    return {'status': 'success', 'message': f'Session {session_id} reset successfully.'}

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)
