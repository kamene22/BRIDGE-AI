import os, time
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

models = [m.name for m in genai.list_models() if 'embedContent' in m.supported_generation_methods]
print("Supported embedding models:", models)

for m_name in models:
    try:
        t0 = time.time()
        res = genai.embed_content(model=m_name, content=["test query"])
        print(f"SUCCESS {m_name}: {round((time.time()-t0)*1000)}ms | Dim: {len(res['embedding'][0])}")
    except Exception as e:
        print(f"FAILED {m_name}: {e}")
