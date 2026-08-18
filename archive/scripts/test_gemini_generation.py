import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-2.0-flash")

prompt = """Previous conversation:
Assistant: Have you already had your first 1-on-1 check-in with your manager?
User: not yet what should I expect

User question: not yet what should I expect"""

sys_prompt = "You are Amani, a warm career mentor. Continue the conversation naturally."

res = model.generate_content(prompt)
print("Gemini Response:\n", res.text)
