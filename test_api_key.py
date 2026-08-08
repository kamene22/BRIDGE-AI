#!/usr/bin/env python3
"""Minimal raw API test — bypasses all pipeline code to isolate the generation issue."""
import sys
sys.stdout.reconfigure(line_buffering=True)

import os
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GENERATION_MODEL", "gemini-2.0-flash-lite")
print(f"Key loaded: {api_key[:20]}...")
print(f"Model:      {model_name}")

genai.configure(api_key=api_key)

print(f"Calling {model_name}...")
try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Say exactly: Bridge AI pipeline is live and working.")
    print(f"\nResponse: {response.text}")
    print("\n✓ Generation API working with new key!")
except Exception as e:
    print(f"\n✗ Error: {e}")
