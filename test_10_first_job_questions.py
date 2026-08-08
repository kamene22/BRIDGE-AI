"""
test_10_first_job_questions.py — Evaluation test suite for 10 realistic first job questions
"""

import sys
import os

sys.path.insert(0, os.path.abspath("src"))
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()

questions = [
    "I got my first job. What should I know?",
    "What should I wear on my first day?",
    "What should I bring on my first day?",
    "How do I introduce myself to my new team?",
    "What if I don't know how to do my work?",
    "Is it okay to ask a lot of questions?",
    "How do I make a good first impression?",
    "What mistakes should I avoid during my first week?",
    "How can I earn my manager's trust?",
    "How do I fit into a new workplace quickly?"
]

print("=" * 80)
print("EVALUATING 10 REALISTIC FIRST JOB CAREER QUESTIONS")
print("=" * 80)

for i, q in enumerate(questions, start=1):
    print(f"\n[{i}/10] User Query: \"{q}\"")
    print("-" * 75)
    res = pipeline.run(q)
    ans = res["answer"]
    print(f"💬 Amani Mentor Response:\n{ans}\n")
    print("-" * 75)

print("=" * 80)
print("ALL 10 FIRST JOB QUESTIONS EVALUATED SUCCESSFULLY ✓")
print("=" * 80)
