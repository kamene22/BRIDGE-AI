
from google import genai
import os, dotenv
dotenv.load_dotenv('/home/monic/projects/BridgeAI/.env')
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
print('LISTING MODELS:')
for m in client.models.list():
    methods = getattr(m, 'supported_generation_methods', [])
    if 'bidiGenerateContent' in methods or any(k in m.name.lower() for k in ['flash', 'live', 'exp', '2.0', '3.1']):
        print('MODEL:', m.name, 'METHODS:', methods)
