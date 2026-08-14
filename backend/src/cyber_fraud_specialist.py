import logging
import json
import asyncio
from livekit.agents import Agent, function_tool
from db import get_caller, save_caller, create_escalation

logger = logging.getLogger("agent.fraud_specialist")

CYBER_FRAUD_SYSTEM_PROMPT = """
# IDENTITY
You are FinBuddy's Cyber Fraud and Financial Safety Specialist.
Your ONLY job is to help users who report:
- UPI scams
- Phishing
- Suspicious payment requests
- Fake bank calls
- Fake customer-care numbers
- Investment scams
- Loan scams
- OTP scams
- Card/payment fraud
- Suspicious links
- Impersonation scams
- Account compromise concerns
- Digital financial fraud

Your priority is immediate safety and clear next steps.

# REASSURANCE & RESPONSE FLOW
When a caller reports suspected fraud:
1. Stay calm and reassuring.
2. Tell them not to share additional sensitive information.
3. Provide general immediate safety guidance (e.g. do not share OTP/PIN/password, stop interacting with suspicious callers, avoid clicking suspicious links, contact their bank through official channels).
4. Help identify what type of scam it may be.
5. Explain appropriate next steps without pretending to be a bank, police officer, or government authority.
6. If human assistance is needed, use the existing escalation flow after obtaining explicit consent.

# NO FALSE ACTION CLAIMS
- Never say: "I have blocked your account." or "I have contacted your bank." or "I have reported this to cybercrime." or "I have frozen the transaction."
- Instead say: "You should contact your bank through its official customer-care channel." or "You should report this on the official National Cyber Crime Reporting Portal."

# LIMITS & GUARDRAILS
- **CRITICAL**: Never ask for or accept OTP, PIN, UPI PIN, password, CVV, bank account number, debit card number, credit card number, Aadhaar number, PAN number, or authentication credentials.
- **CRITICAL**: If the user provides sensitive information:
  - Do NOT repeat it.
  - Do NOT store it.
  - Do NOT pass it to another agent.
  - Do NOT include it in an escalation summary.
  - Say: "For your security, please don't share OTPs, PINs, passwords or banking credentials with me."

# LANGUAGE & SCRIPTS
- Always respond in the user's current/detected language.
- Supported languages: English, Hindi, Tamil, Telugu.
- Always write non-English languages using their correct native script:
  - English -> Latin script
  - Hindi -> Devanagari script (e.g. "नमस्ते...") - NEVER Romanized.
  - Tamil -> Tamil script (e.g. "வணக்கம்...") - NEVER Romanized.
  - Telugu -> Telugu script (e.g. "నమస్కారం...") - NEVER Romanized.
- The user's input may be code-mixed or Romanized (e.g. "Enakku scam call vandhudhu"). Understand it naturally, but respond in the correct native script. Never simply mirror Romanized Indian languages.

# OUT-OF-ROLE TOPICS
If the user changes topic to something outside your role (such as government scheme details, general financial literacy, budgeting, savings, compound interest, banking, or digital payments), or explicitly asks to connect/talk to the assistant, you MUST call the `return_to_main_agent` tool immediately. Do not try to answer these yourself.
If you cannot call it, politely say:
"I specialize in cyber fraud and financial safety. For that question, FinBuddy's general financial assistant may be better suited."
Do NOT hand off back or loop. Just state this response.
"""

class CyberFraudSpecialist(Agent):
    def __init__(self, main_assistant, user_id: str = "default_user", language: str = "English", user_query: str = None, intent: str = None) -> None:
        self.main_assistant = main_assistant
        self.user_id = user_id
        self.language = language
        self.user_query = user_query
        self.intent = intent
        
        # Inject dynamic context parameters to prompt to greet user and answer immediately without asking
        instructions = CYBER_FRAUD_SYSTEM_PROMPT
        if user_query:
            instructions += f"\n\n# ACTIVE CONTEXT\n- Original User Query: {user_query}\n"
        if intent:
            instructions += f"- Suspected Scam Intent: {intent}\n"
        if language:
            instructions += f"- Detected Language: {language}\n"
            
        instructions += f"\n- Current User ID: {user_id}\n"
        
        # Specialist introduction requirements
        intro_dict = {
            "Hindi": "नमस्ते, मैं फिनबड्डी का साइबर धोखाधड़ी और वित्तीय सुरक्षा विशेषज्ञ हूँ। मैं अगले कदम उठाने में आपकी मदद कर सकता हूँ। मैं समझता हूँ कि आपको धोखाधड़ी का सामना करना पड़ा है। चलिए मैं इसमें आपकी मदद करता हूँ।",
            "Tamil": "வணக்கம், நான் பின்படியின் சைபர் மோசடி மற்றும் நிதி பாதுகாப்பு நிபுணர். அடுத்த கட்ட நடவடிக்கைகளுக்கு நான் உங்களுக்கு உதவ முடியும். உங்களுக்கு மோசடி நேர்ந்திருப்பதாக நான் உணர்கிறேன். அதற்கு நான் உதவுகிறேன்.",
            "Telugu": "నమస్కారం, నేను ఫిన్‌బడ్డీ సైబర్ మోసాలు మరియు ఆర్థిక భద్రత నిపుణుడిని. తదుపరి చర్యలలో నేను సహాయం చేయగలను. మీకు మోసం జరిగిందని నేను గ్రహించాను. దానికి నేను సహాయం చేస్తాను.",
            "English": "Hello, I'm FinBuddy's cyber fraud and financial safety specialist. I can help you with the next steps. I understand you're dealing with a suspicious situation. Let me help with that."
        }
        greeting = intro_dict.get(language, intro_dict["English"])
        instructions += f"\n\n# FIRST-TURN GREETING\nYou must welcome the user and offer safety advice immediately based on the active context. Greet them EXACTLY with this greeting:\n\"{greeting}\"\n"
        
        super().__init__(instructions=instructions)

    @function_tool
    async def return_to_main_agent(
        self,
        user_query: str,
        intent: str,
        language: str
    ) -> str:
        """Return the conversation back to FinBuddy's main general financial assistant when the user asks a question outside cyber fraud/safety (such as government schemes, general financial concepts, budgeting, savings, compound interest, banking, digital payments) or explicitly asks to talk to the general assistant.
        
        Args:
            user_query: The user's query that is outside cyber fraud/safety.
            intent: The detected intent category (e.g. GOVERNMENT_SCHEME, GENERAL).
            language: The user's preferred language.
        """
        logger.info(f"CyberFraudSpecialist: Returning to main agent. Query: {user_query}, Intent: {intent}")
        
        if intent == "GOVERNMENT_SCHEME":
            announcement = "Understood. This is better handled by our government scheme specialist. I'll connect you now."
            intro_dict = {
                "Hindi": "मैं समझता हूँ। यह हमारे सरकारी योजना विशेषज्ञ द्वारा बेहतर ढंग से संभाला जा सकता है। मैं आपको अभी जोड़ता हूँ।",
                "Tamil": "புரிந்துகொண்டேன். இதை எங்கள் அரசு திட்ட நிபுணர் சிறப்பாகக் கையாள முடியும். நான் உங்களை இப்போது இணைக்கிறேன்.",
                "Telugu": "అర్థమైంది. ఇది మా ప్రభుత్వ పథకాల నిపుణుడి ద్వారా మెరుగ్గా నిర్వహించబడుతుంది. నేను మిమ్మల్ని ఇప్పుడు కనెక్ట్ చేస్తాను."
            }
            announcement = intro_dict.get(language, announcement)
            self.main_assistant.queued_handoff_query = user_query
            self.main_assistant.queued_handoff_intent = intent
        else:
            announcement = "Connecting you back to our general financial assistant."
            self.main_assistant.queued_handoff_query = user_query
            self.main_assistant.queued_handoff_intent = "GENERAL"
            
        try:
            session = self.main_assistant.session
        except RuntimeError:
            session = getattr(self.main_assistant, "_session", None)
            
        if session:
            try:
                # Speak announcement in the current agent's voice before handoff
                handle = await session.say(announcement, allow_interruptions=False)
                await handle.wait_for_playout()
            except Exception as e:
                logger.error(f"Error playing handback announcement: {e}")
                
            try:
                session.tts.update_options(voice="Anisha")
            except Exception as e:
                logger.error(f"Error resetting voice to Anisha: {e}")
            session.update_agent(self.main_assistant)

            
        return json.dumps({
            "success": True,
            "message": announcement
        })



    @function_tool
    async def lookup_caller(self, user_id: str) -> str:
        """Look up details of a caller by user_id to see their name, language preference, and history.
        
        Args:
            user_id: The unique identifier/phone number of the caller.
        """
        logger.info(f"Cyber Fraud Specialist: Looking up caller with user_id: {user_id}")
        caller = get_caller(user_id)
        if caller:
            return json.dumps(caller)
        return "No record found."

    @function_tool
    async def save_caller_details(
        self,
        user_id: str,
        name: str,
        language_preference: str,
        schemes_checked: str,
        eligibility_answers: str,
    ) -> str:
        """Saves caller details to database.
        
        CRITICAL: Ask the caller first before saving. If they say no, do NOT run this function.
        
        Args:
            user_id: The unique identifier/phone number of the caller.
            name: Name of the caller.
            language_preference: The caller's preferred language.
            schemes_checked: Schemes already checked. Do NOT store account or ID numbers.
            eligibility_answers: Eligibility answers.
        """
        logger.info(f"Cyber Fraud Specialist: Saving caller details for {user_id} - {name}")
        facts = {
            "schemes_checked": schemes_checked,
            "eligibility_answers": eligibility_answers
        }
        save_caller(user_id, name, language_preference, facts)
        return "Successfully saved details."

    @function_tool
    async def create_escalation(
        self,
        user_id: str,
        issue_summary: str,
        what_happened: str,
        agent_checks: str,
        urgency: str,
        language: str,
        preferred_follow_up: str,
        caller_name: str = None
    ) -> str:
        """Create a human escalation request when genuine help is needed.
        
        Use this tool when the user requires account-specific assistance, or reports scams, or needs actions you cannot perform.
        
        CRITICAL: NEVER create an escalation request without obtaining explicit user consent first.
        """
        logger.info(f"Cyber Fraud Specialist: create_escalation tool called for user {user_id}")
        
        # Defer to main assistant's implementation to preserve exact logic and safety scrubbing
        return await self.main_assistant.create_escalation(
            user_id=user_id,
            issue_summary=issue_summary,
            what_happened=what_happened,
            agent_checks=agent_checks,
            urgency=urgency,
            language=language,
            preferred_follow_up=preferred_follow_up,
            caller_name=caller_name
        )
