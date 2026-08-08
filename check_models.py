import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print(f"API Key present: {bool(key)}")

if key:
    genai.configure(api_key=key)
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    print("Testing generateContent on models:", models)
    for m_name in models:
        try:
            mod = genai.GenerativeModel(m_name)
            res = mod.generate_content("Hello")
            print(f"SUCCESS with {m_name}: {res.text[:50]}")
            break
        except Exception as e:
            print(f"FAILED {m_name}: {e}")
