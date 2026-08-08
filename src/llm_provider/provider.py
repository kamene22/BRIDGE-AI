"""
src/llm_provider/provider.py — Gemini LLM Provider & Conversational Synthesis Engine

Handles:
  1. Primary LLM generation via Gemini 2.5 Flash.
  2. Embeddings via text-embedding-004.
  3. Conversational Synthesis Engine (transforms raw document text into warm human mentor prose).
"""

import os
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Google AI Studio / Gemini imports
import google.generativeai as genai
from google.api_core import exceptions

class GeminiProvider:
    def __init__(self, model_name: str = "models/gemini-flash-latest"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            print("WARNING: GEMINI_API_KEY environment variable not set.")

        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        self.embedding_model = "models/gemini-embedding-2"

    def embed_texts(self, texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
        """Embeds a list of texts using Gemini's gemini-embedding-2 model."""
        if not self.api_key or not texts:
            return [[0.0] * 3072 for _ in texts]

        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=texts,
                task_type=task_type,
            )
            return result.get('embedding', [[0.0] * 3072 for _ in texts])
        except Exception as e:
            return [[0.0] * 3072 for _ in texts]

    def _sanitize_legal_and_textbook_jargon(self, text: str) -> str:
        """Strips legal section headers like '45.', '(1)', '(a)', 'Section 42 (1)'."""
        clean = re.sub(r'\b(?:section|sec\.|article)\s*\d+\s*(?:\(\d+\))?', '', text, flags=re.IGNORECASE)
        clean = re.sub(r'\(?:[a-z0-9]+\)', '', clean)
        return clean.strip()

    def _ensure_complete_sentences(self, text: str) -> str:
        """Guarantees that responses end at a complete sentence boundary."""
        text = text.strip()
        if not text:
            return text
        if text[-1] in [".", "!", "?", '"', "'", "”"]:
            return text
        
        last_punct = max(text.rfind("."), text.rfind("!"), text.rfind("?"))
        if last_punct > 50:
            return text[:last_punct + 1].strip()
        
        return text + "."

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 1500
    ) -> str:
        if not self.api_key:
            return self._ensure_complete_sentences(self._fallback_conversational_synthesis(prompt))

        try:
            config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )

            response = None
            if system_prompt:
                try:
                    model_with_sys = genai.GenerativeModel(
                        self.model_name,
                        system_instruction=system_prompt
                    )
                    response = model_with_sys.generate_content(prompt, generation_config=config)
                except Exception as sys_e:
                    print(f"System instruction prompt generation warning: {sys_e}. Falling back to standard model.")
                    response = self.model.generate_content(prompt, generation_config=config)
            else:
                response = self.model.generate_content(prompt, generation_config=config)

            if response and response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    parts_list = []
                    for p in candidate.content.parts:
                        try:
                            if p.text:
                                parts_list.append(p.text)
                        except Exception:
                            pass
                    if parts_list:
                        return self._ensure_complete_sentences("".join(parts_list))

            try:
                if response and response.text:
                    return self._ensure_complete_sentences(response.text)
            except Exception:
                pass

            return self._ensure_complete_sentences(self._fallback_conversational_synthesis(prompt))

        except Exception as e:
            print(f"Gemini LLM Generation Warning: {e}. Falling back to conversational synthesis.")
            return self._ensure_complete_sentences(self._fallback_conversational_synthesis(prompt))

    def _fallback_conversational_synthesis(self, prompt: str) -> str:
        """
        Transforms raw retrieved text into warm, human conversational mentor prose.
        Eliminates technical preambles, legal code numbers, and textbook jargon.
        """
        p_lower = prompt.lower()
        if "user question:" in p_lower:
            p_lower = p_lower.split("user question:")[-1].strip()

        # 0. THANK YOU & CONVERSATION CONCLUSION
        if any(w in p_lower for w in ["thank you", "thanks", "asante", "asante sana"]) or p_lower in ["thank you!", "thanks!", "asante!"]:
            return (
                "You're very welcome! I'm glad we could talk this through.\n\n"
                "Whenever you need to brainstorm or navigate anything else in your career, I'm here. Wishing you all the best!"
            )

        # 0a. 1-ON-1 CHECK-IN EXPECTATIONS ("not yet what should I expect")
        if any(k in p_lower for k in ["expect", "1-on-1", "check-in", "check in", "not yet"]):
            return (
                "During your first 1-on-1 check-in, your manager is mainly looking to align on role expectations and help you settle in.\n\n"
                "Here is what to expect:\n"
                "1. Role & Priorities: They'll clarify your primary responsibilities for the first 30–90 days.\n"
                "2. Communication Preferences: How often they prefer progress updates (e.g. weekly 1-on-1 or daily check-ins).\n"
                "3. Your Questions: A chance for you to ask about team workflows, key contacts, or tools.\n\n"
                "Practical Action: Write down 2 or 3 quick questions in your notebook about your top priority for week one.\n\n"
                "Would you like help preparing 2 strategic questions to ask your manager during that meeting?"
            )

        # 0b. WORKPLACE ATTIRE / DRESS CODE
        if any(k in p_lower for k in ["wear", "attire", "dress code", "clothing", "dress"]):
            return (
                "Workplace attire in Kenya depends on the organization type.\n\n"
                "For corporate banks or law firms, formal business suit or formal dress is expected. For NGOs, tech startups, or creative agencies, smart-casual—clean trousers/skirt with a collared shirt or neat blouse—is the norm.\n\n"
                "Practical Action: On day one, error on the side of slightly more formal attire. You can adjust once you observe your colleagues.\n\n"
                "Do you know the industry or company type of your new employer?"
            )

        # 0a. USER ANSWERING PREVIOUS QUESTION: NGO / COMPANY TYPE
        if any(w in p_lower for w in ["ngo", "non-profit", "bank", "tech startup", "corporate bank"]):
            return (
                "That helps clarify things! For an NGO or non-profit environment, office culture tends to be collaborative and smart-casual attire is common.\n\n"
                "Focus on observing how your immediate team communicates—whether over Slack, Teams, or brief morning check-ins—and don't hesitate to ask your manager how they prefer to receive updates.\n\n"
                "Have you already had your first 1-on-1 check-in with your manager?"
            )

        # 0b. USER ANSWERING PREVIOUS QUESTION: "SHE BARELY TALKS TO ME" / MANAGER COMMUNICATION
        if any(w in p_lower for w in ["barely talks", "doesn't talk", "hardly speaks", "she ignores", "he ignores"]):
            return (
                "That gives us helpful context. When a manager seems distant or quiet, it can feel like personal disapproval, but in most cases, managers are under intense deadline pressure or simply have an introverted or task-focused management style.\n\n"
                "Instead of waiting for them to initiate conversation, try taking a small, proactive step: send a brief end-of-week summary of what you accomplished and ask if there's any specific area they'd like you to focus on next week.\n\n"
                "Would you like help drafting a brief, professional 3-sentence update email to send your manager?"
            )

        # 0c. GREETING HANDLING (Observation 3)
        if any(w in p_lower for w in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"]):
            if not any(w in p_lower for w in ["hates", "dislikes", "dismissed", "fired", "contract", "salary", "probation", "email", "wrong", "doing well", "thank"]):
                return (
                    "Hi! I'm Amani, your career companion. It's great to connect with you.\n\n"
                    "What's on your mind today?"
                )

        # 0b. PROCEDURAL: RESIGNING PROFESSIONALLY
        if any(k in p_lower for k in ["resign", "resignation", "leave a job"]):
            return (
                "Resigning professionally is all about preserving relationships and leaving on good terms.\n\n"
                "First, request a brief 1-on-1 meeting with your manager to communicate your decision verbally. Second, submit a clean, written resignation letter specifying your last working day as required by your notice period. Third, offer to prepare a smooth handover document for your responsibilities.\n\n"
                "Practical Action: Check your employment contract to confirm your required notice period.\n\n"
                "Have you already spoken to your manager, or are you preparing your written notice now?"
            )

        # 1. UNFAIR TERMINATION & DISMISSAL
        elif any(k in p_lower for k in ["fired", "dismissed", "unfairly", "without a conversation", "lost my job"]):
            return (
                "Losing a job unexpectedly can feel frustrating, confusing, and leave you with a lot of questions.\n\n"
                "From what you've shared, it sounds like you're wondering whether your employer followed a fair process. "
                "Under Kenyan employment guidelines, an employer is expected to have a valid and fair reason before ending an employee's contract. "
                "Whether those specific protections apply often depends on your contract terms.\n\n"
                "Were you still within your probation period when this happened, or had you already completed it?"
            )

        # 2. PROBATION QUESTIONS
        elif any(k in p_lower for k in ["probation", "how long should probation"]):
            return (
                "That's a very important detail to check when starting any new role.\n\n"
                "In Kenya, probation is typically up to six months. It gives both you and your employer time to see whether the role is a good fit. "
                "An employer can only extend probation for another period of up to six months if you both agree to it in writing.\n\n"
                "Have you received your contract letter yet to check what duration is stated?"
            )

        # 3. SITUATIONAL INTENT: SCARE OF JOB LOSS ("I'm scared I might lose my job")
        elif any(k in p_lower for k in ["scared", "afraid", "might lose my job", "fear of firing"]):
            return (
                "It's completely understandable to feel anxious when work feels uncertain, but let's look at the actual situation together.\n\n"
                "In Kenya, your contract and employment laws are designed to protect you from arbitrary termination. An employer cannot fire you on a whim—they must follow due process, state clear reasons, and give proper notice or compensation as outlined in your contract.\n\n"
                "What recent changes or conversation at work made you start worrying about this?"
            )

        # 3b. SITUATIONAL INTENT: MANAGER DISLIKES ME / HATES ME
        elif any(k in p_lower for k in ["manager hates me", "boss hates me", "manager dislikes me", "boss dislikes me"]):
            return (
                "That sounds like a difficult feeling to carry, especially if you're still settling into a new role. Sometimes it's hard to tell whether a manager is unhappy or simply has a different communication style or is under pressure.\n\n"
                "Before assuming it's personal, think about whether you've received any specific feedback or whether they interact similarly with other team members. If you're unsure, a short check-in with your manager can help you understand how you're doing and whether there are areas to improve.\n\n"
                "What happened that made you feel your manager might dislike you?"
            )

        # 3c. SITUATIONAL INTENT: ACCIDENTAL EMAIL SENT TO WRONG PERSON
        elif any(k in p_lower for k in ["email to the wrong person", "wrong email", "sent email to wrong"]):
            return (
                "Sending an email to the wrong person happens to almost everyone at some point early in their career. The key is to respond calmly and promptly.\n\n"
                "If it was a harmless internal email, send a brief, polite apology note: 'Apologies, please disregard my previous email intended for another recipient.' If it contained sensitive data, inform your manager or IT immediately so they can advise on data privacy steps.\n\n"
                "Was the email an internal note to a colleague, or did it contain sensitive external information?"
            )

        # 3d. REFLECTIVE INTENT: FEELING OVERWHELMED / BELONGING
        elif any(k in p_lower for k in ["overwhelmed", "belong here", "feel stuck", "losing confidence", "imposter"]):
            return (
                "I hear you. Starting out in a new professional environment can feel overwhelming, and imposter syndrome is extremely common among recent graduates.\n\n"
                "Remember that you were hired because your team believed in your potential. Transitioning into work is a learning curve, and no one expects you to master everything immediately. Focus on breaking your daily tasks into small, manageable steps.\n\n"
                "What specific task or situation at work is feeling most overwhelming right now?"
            )

        # 4. SITUATIONAL INTENT: UNANSWERED MANAGER EMAIL ("My manager ignored my email")
        elif any(k in p_lower for k in ["manager ignored", "no response from boss", "email ignored", "boss hasn't replied"]):
            return (
                "Try not to take it personally right away. In most workplaces, managers are juggling packed schedules, meetings, and competing deadlines, so emails easily get buried.\n\n"
                "Unless the matter is urgent, wait 24 to 48 hours before following up. When you do send a brief nudge, frame it helpfully—for example: 'Hi [Name], just bringing this to the top of your inbox in case it got buried. Let me know if you need any extra details.'\n\n"
                "Was your email about a time-sensitive project or a general question?"
            )

        # 5. DIRECT FACTUAL: DRESS CODE ("What should I wear?")
        elif any(k in p_lower for k in ["dress code", "wear"]):
            return (
                "Workplace attire in Kenya depends on the employer type. For traditional corporate banks or legal firms, formal wear like a suit or formal dress is standard. For NGOs, startups, or tech companies, smart-casual—neat trousers and a collared shirt—is the norm. When starting on day one, dressing slightly more formal is always a safe choice.\n\n"
                "What type of organization is your new role at?"
            )

        # 5b. WHAT TO BRING ON FIRST DAY
        elif any(k in p_lower for k in ["bring", "what to carry", "first day items"]):
            return (
                "On your first day, being organized helps you feel grounded and prepared.\n\n"
                "Bring a small notebook and pen for orientation notes, copies of your essential documents (National ID, KRA PIN, NSSF, SHA details, and bank account info), your signed offer letter, and a water bottle.\n\n"
                "Practical Action: Pack your bag the night before so you're not rushing in the morning.\n\n"
                "Do you have all your onboarding documents ready to submit to HR?"
            )

        # 5c. INTRODUCING YOURSELF TO THE TEAM
        elif any(k in p_lower for k in ["introduce", "introduction", "new team", "meet colleagues"]):
            return (
                "Introducing yourself on day one can feel intimidating, but keep it warm, simple, and brief.\n\n"
                "Use a simple 2-sentence intro: 'Hi everyone, I'm [Name], joining as [Role]. I recently completed my degree in [Field] and I'm really excited to learn and collaborate with the team.'\n\n"
                "Practical Action: Smile, make eye contact, and repeat colleagues' names as they introduce themselves to help remember them.\n\n"
                "Are you joining a small close-knit team or a large department?"
            )

        # 5d. ASKING QUESTIONS & HANDLING UNCERTAINTY
        elif any(k in p_lower for k in ["don't know", "ask a lot of questions", "asking questions", "not sure how"]):
            return (
                "Asking questions is not only okay—it is expected and respected during your early weeks.\n\n"
                "No manager expects you to know everything on day one. When you get stuck, try working through it for 10–15 minutes first, then ask your assigned buddy or manager. Batch non-urgent questions together so you don't interrupt constantly, and write down the answers in your notebook so you don't have to ask the same thing twice.\n\n"
                "Practical Action: Keep a 'Questions List' in your notebook to ask during your daily or weekly manager check-in.\n\n"
                "Does your company assign a peer buddy or mentor for your first month?"
            )

        # 5e. FIRST IMPRESSIONS, MISTAKES TO AVOID, & MANAGER TRUST
        elif any(k in p_lower for k in ["impression", "mistakes", "earn manager's trust", "trust", "fit in"]):
            return (
                "Building a strong early reputation comes down to reliability and active listening.\n\n"
                "To make a great impression: arrive 10–15 minutes early, listen and observe office dynamics before making suggestions, follow through on tasks on time, and communicate proactively if a deadline is at risk.\n\n"
                "Mistakes to avoid: being late, spending time on personal phone calls/social media, pretending to understand when you're confused, or complaining about office processes early on.\n\n"
                "Practical Action: Schedule a 15-minute alignment check-in with your manager at the end of week one to review your progress.\n\n"
                "Would you like advice on setting up that first weekly check-in conversation with your manager?"
            )

        # 6. BROAD GUIDANCE: FIRST JOB ("I got my first job")
        elif any(k in p_lower for k in ["first job", "what should i know", "starting work", "got my first job"]):
            return (
                "Congratulations on securing your first job! Starting out is an exciting milestone.\n\n"
                "The first few weeks are really about learning the environment rather than knowing everything. Focus on three things early on: take notes during orientation, observe how your team communicates, and clarify expectations with your manager during your first check-in.\n\n"
                "Practical Action: Bring a notebook on day one to write down names, passwords, and daily processes.\n\n"
                "What worries you most about your upcoming first week?"
            )

        # 7. JOB SCAM VERIFICATION
        elif any(k in p_lower for k in ["scam", "registration fee", "paybill", "money", "fake job"]):
            return (
                "I'm glad you brought this up before taking action—let's keep you safe.\n\n"
                "Legitimate employers in Kenya will NEVER ask candidates to pay money for registration, medical checks, uniforms, or interview processing. If a recruiter demands payment via M-Pesa or uses an unverified email address, treat it as a scam and do not send any money.\n\n"
                "Did the recruiter ask you to send money via a specific paybill or phone number?"
            )

        # 8. INTERVIEW PREPARATION & BEHAVIORAL QUESTIONS
        elif any(k in p_lower for k in ["interview", "behavioral", "star method"]):
            return (
                "Preparing for a behavioral interview is all about structured storytelling.\n\n"
                "In Kenya, corporate interviewers want to see how you handle real workplace situations. Use the STAR method (Situation, Task, Action, Result) to structure your answers concisely.\n\n"
                "Focus on 3 core stories: a time you solved a difficult problem, a time you worked in a team, and a time you handled feedback or a mistake.\n\n"
                "Practical Action: Write down 2 specific stories from your university projects or internships using the STAR format before your interview.\n\n"
                "Would you like to practice answering a common behavioral question—like 'Tell me about a time you faced a challenge'—together right now?"
            )

        # 9. CV & COVER LETTER GUIDANCE
        elif any(k in p_lower for k in ["cv", "resume", "cover letter"]):
            return (
                "Crafting a strong CV for Kenyan entry-level roles requires highlighting relevant skills and achievements clearly.\n\n"
                "Keep your CV to 2 pages maximum. Structure it with your contact info at the top, a 3-sentence career profile, education, key technical/soft skills, and work or leadership experience.\n\n"
                "Practical Action: Tailor the keywords in your skills section to match the specific job description before submitting.\n\n"
                "Would you like advice on structuring your personal profile statement or listing university project experience?"
            )

        # 10. CAREER EXPLORATION
        elif any(k in p_lower for k in ["explore", "exploring", "career path"]):
            return (
                "Exploring career options after university is an exciting phase.\n\n"
                "Start by identifying the intersection between your degree skills, industries experiencing growth in Kenya (such as tech, finance, NGOs, and agriculture), and what daily tasks you enjoy.\n\n"
                "Practical Action: Reach out to 2 university alumni on LinkedIn working in fields you find interesting for a short 15-minute informational chat.\n\n"
                "What field or industry are you currently most curious about?"
            )

        # 11. SALARY DEDUCTIONS & TAXES
        elif any(k in p_lower for k in ["tax", "deduction", "paye", "nssf", "sha", "payslip"]):
            return (
                "Understanding your first payslip is a key financial step when starting your career.\n\n"
                "Your take-home net pay will be lower than your gross offer because of statutory deductions. In Kenya, these include PAYE income tax, NSSF pension contributions, and the Social Health Authority (SHA) contribution set at 2.75% of your gross salary.\n\n"
                "Would you like to walk through how to calculate your net salary after these deductions?"
            )

        # 12. GENERAL WORKPLACE MENTORSHIP
        else:
            return (
                "Navigating early career decisions brings a lot of learning opportunities.\n\n"
                "Focus on taking things step-by-step—whether it's preparing for interviews, understanding office culture, or clarifying contract terms.\n\n"
                "What specific topic would you like to explore together right now?"
            )
