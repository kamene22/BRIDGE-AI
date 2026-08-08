import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from generation.prompt_builder import build_full_prompt

sample_chunks = [
    {
        "document": "42. Termination of probationary contracts\n(1) A probationary period shall not be more than six months but it may be extended for a further period of not more than six months with the agreement of the employee.",
        "metadata": {
            "title": "Employment Act 2007",
            "source": "Employment Act.pdf",
            "page": 29
        }
    },
    {
        "document": "Formality varies significantly by employer type. Banks and traditional corporates typically expect full formal wear — suits, closed shoes. NGOs and development organizations are often smart-casual.",
        "metadata": {
            "title": "Hidden Curriculum Kenya",
            "source": "hidden_curriculum_kenya.md",
            "start_line": 17,
            "end_line": 21
        }
    }
]

query = "What should I expect during my probation period in Kenya?"

system_prompt, user_prompt = build_full_prompt(query, sample_chunks)

print(system_prompt)
print("=" * 80)
print(user_prompt)
