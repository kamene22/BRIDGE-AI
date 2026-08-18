import json
import os

GOLDEN_SET_PATH = "/home/monic/projects/BridgeAI/evaluation/golden_eval_set.json"
OUTPUT_PATH = "/home/monic/projects/BridgeAI/evaluation/retrieval_eval_set.json"

with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
    golden_cases = json.load(f)

# Ground-truth source and fact annotations for retrieval-required test cases
retrieval_ground_truth = {
    "GE-001": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["probation", "six months", "6 months", "section 42", "extended"],
        "required_facts": ["probation capped at 6 months", "extension must be in writing", "Employment Act"]
    },
    "GE-002": {
        "expected_source": "first_salary_financial_literacy.md",
        "expected_chunk_keywords": ["paye", "nssf", "sha", "shif", "deductions", "payslip"],
        "required_facts": ["PAYE income tax", "NSSF pension", "SHIF/SHA health contribution", "net pay"]
    },
    "GE-003": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["probation", "notice", "termination", "seven days", "7 days"],
        "required_facts": ["notice period during probation", "7 days notice or pay in lieu", "Employment Act"]
    },
    "GE-004": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["minimum wage", "regulation of wages", "nairobi", "order"],
        "required_facts": ["varies by location and job category", "Regulation of Wages Act", "Ministry of Labour"]
    },
    "GE-005": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["written contract", "statement of particulars", "two months", "three months"],
        "required_facts": ["written contract required by law", "right to written terms", "Ministry of Labour"]
    },
    "GE-006": {
        "expected_source": "first_salary_financial_literacy.md",
        "expected_chunk_keywords": ["deduction", "dock", "pay", "unauthorized", "salary"],
        "required_facts": ["wage deductions must be authorized", "limited lawful grounds", "Employment Act"]
    },
    "GE-007": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["hours", "working hours", "52 hours", "overtime", "week"],
        "required_facts": ["maximum normal working hours", "overtime compensation", "52 hours per week"]
    },
    "GE-008": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["leave", "annual leave", "21 days", "sick leave", "maternity"],
        "required_facts": ["21 working days annual leave", "sick leave entitlement", "maternity/paternity leave"]
    },
    "GE-009": {
        "expected_source": "bridge_ai_career_handbook_expanded.md",
        "expected_chunk_keywords": ["contract", "signing", "probation", "job title", "salary"],
        "required_facts": ["check salary and pay date", "check probation clause duration", "confirm job title and duties"]
    },
    "GE-010": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["termination", "notice", "summary dismissal", "fair reason", "procedural fairness"],
        "required_facts": ["employer needs valid reason", "written notice or pay in lieu", "procedural hearing requirement"]
    },
    "GE-011": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["probation", "extension", "section 42", "written agreement"],
        "required_facts": ["probation extension rules", "written consent required", "maximum cap"]
    },
    "GE-012": {
        "expected_source": "hidden_curriculum_kenya.md",
        "expected_chunk_keywords": ["mistake", "wrong person", "email", "manager", "apologize"],
        "required_facts": ["inform manager/recipient promptly", "send concise written correction", "avoid panic"]
    },
    "GE-013": {
        "expected_source": "hidden_curriculum_kenya.md",
        "expected_chunk_keywords": ["1-on-1", "check-in", "manager", "priorities", "questions"],
        "required_facts": ["align on first 30-90 day priorities", "ask about communication preferences", "prepare specific questions"]
    },
    "GE-014": {
        "expected_source": "job_scam_red_flags.md",
        "expected_chunk_keywords": ["scam", "paybill", "upfront fee", "training kit", "mpesa"],
        "required_facts": ["never pay upfront fees for hiring", "verify employer domain/office", "common red flags in Kenya"]
    },
    "GE-015": {
        "expected_source": "nea_career_services_guide.md",
        "expected_chunk_keywords": ["ajira", "nea", "digital", "government", "registration"],
        "required_facts": ["free government digital skills portal", "online work opportunities", "no payment required"]
    },
    "GE-016": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["probation", "extension", "six months", "written"],
        "required_facts": ["probation maximum limits", "written agreement for extension"]
    },
    "GE-017": {
        "expected_source": "Employment Act.pdf",
        "expected_chunk_keywords": ["probation", "refuse", "termination", "notice"],
        "required_facts": ["rights when declining extension", "notice terms apply"]
    },
    "GE-018": {
        "expected_source": "hidden_curriculum_kenya.md",
        "expected_chunk_keywords": ["manager", "1-on-1", "meeting", "ignored", "schedule"],
        "required_facts": ["polite follow-up nudge", "proactive status update"]
    },
    "GE-019": {
        "expected_source": "hidden_curriculum_kenya.md",
        "expected_chunk_keywords": ["email", "ignored", "nudge", "follow up", "inbox"],
        "required_facts": ["wait 24-48 hours", "send brief professional follow-up"]
    },
    "GE-020": {
        "expected_source": "hidden_curriculum_kenya.md",
        "expected_chunk_keywords": ["dress code", "bank", "startup", "formal", "smart casual"],
        "required_facts": ["corporate bank requires formal attire", "startup is smart casual"]
    },
    "GE-021": {
        "expected_source": "hidden_curriculum_kenya.md",
        "expected_chunk_keywords": ["dress code", "bank", "formal", "suit", "attire"],
        "required_facts": ["formal suit or tailored outfit", "observe office norms"]
    },
    "GE-022": {
        "expected_source": "hidden_curriculum_kenya.md",
        "expected_chunk_keywords": ["dress code", "startup", "tech", "smart casual"],
        "required_facts": ["smart casual attire", "collared shirt / clean trousers"]
    },
    "GE-023": {
        "expected_source": "bridge_ai_career_handbook_expanded.md",
        "expected_chunk_keywords": ["imposter syndrome", "overwhelmed", "belong", "first job"],
        "required_facts": ["focus on manageable tasks", "normal learning curve"]
    },
    "GE-024": {
        "expected_source": "hidden_curriculum_kenya.md",
        "expected_chunk_keywords": ["manager", "feedback", "communication", "distant"],
        "required_facts": ["send weekly status updates", "avoid assuming personal dislike"]
    },
    "GE-025": {
        "expected_source": "job_scam_red_flags.md",
        "expected_chunk_keywords": ["scam", "whatsapp", "unverified", "paybill", "recruiter"],
        "required_facts": ["verify company email domain", "do not send M-Pesa payments"]
    },
    "GE-026": {
        "expected_source": "job_scam_red_flags.md",
        "expected_chunk_keywords": ["scam", "verify", "address", "company registration"],
        "required_facts": ["check physical office location", "search company online"]
    },
    "GE-027": {
        "expected_source": "bridge_ai_career_handbook_expanded.md",
        "expected_chunk_keywords": ["salary", "negotiation", "market rate", "entry level"],
        "required_facts": ["research market benchmarks", "focus on value and skills"]
    },
    "GE-028": {
        "expected_source": "first_salary_financial_literacy.md",
        "expected_chunk_keywords": ["net pay", "take home", "deductions", "paye", "nssf"],
        "required_facts": ["net pay equals gross minus statutory deductions", "budget from net pay"]
    },
    "GE-029": {
        "expected_source": "bridge_ai_career_handbook_expanded.md",
        "expected_chunk_keywords": ["resign", "resignation letter", "notice period", "handover"],
        "required_facts": ["give formal written notice", "prepare smooth handover document"]
    }
}

retrieval_dataset = []
for case in golden_cases:
    if case.get("requires_retrieval", False):
        t_id = case["id"]
        gt = retrieval_ground_truth.get(t_id, {
            "expected_source": "bridge_ai_career_handbook_expanded.md",
            "expected_chunk_keywords": ["career", "workplace", "kenya"],
            "required_facts": ["relevant guidance"]
        })
        retrieval_dataset.append({
            "test_id": t_id,
            "category": case["category"],
            "question": case["question"],
            "conversation_history": case.get("conversation_history", []),
            "requires_retrieval": True,
            "expected_source": gt["expected_source"],
            "expected_chunk_keywords": gt["expected_chunk_keywords"],
            "required_facts": gt["required_facts"],
            "must_include": case.get("must_include", []),
            "must_not_include": case.get("must_not_include", [])
        })

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(retrieval_dataset, f, indent=2)

print(f"Successfully generated {len(retrieval_dataset)} annotated retrieval ground-truth test cases -> {OUTPUT_PATH}")
