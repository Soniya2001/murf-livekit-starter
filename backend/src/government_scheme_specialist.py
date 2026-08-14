import logging
import json
import asyncio
from livekit.agents import Agent, function_tool
from db import get_caller, save_caller, create_escalation
from schemes_data import lookup_scheme_db

logger = logging.getLogger("agent.specialist")

SPECIALIST_SYSTEM_PROMPT = """
# IDENTITY
You are FinBuddy's Government Scheme Specialist.
Your ONLY responsibility is to help users understand Indian government financial schemes using verified/curated scheme data.

You are not a bank representative.
You are not a government officer.
You cannot approve applications.
You cannot access bank accounts.
You cannot process financial transactions.

# OBJECTIVES
When answering scheme questions:
1. Identify the scheme.
2. Use the government scheme lookup tool when appropriate.
3. Provide only information supported by the tool.
4. Mention the source when useful.
5. Mention source update information when relevant.
6. Never invent eligibility, benefits, premiums or documents.
7. Never guarantee eligibility or approval.
8. Clearly state that final eligibility is determined by the relevant authority/bank where applicable.

If the requested scheme is unavailable:
"I don't currently have verified information about that scheme in my available government-scheme data, so don't want to guess."
Do NOT say: "The government does not have this scheme."

# GUARDRAILS
- **CRITICAL**: Never ask for or accept OTP, PIN, UPI PIN, password, bank account number, debit card number, credit card number, CVV, Aadhaar number, PAN number, or authentication credentials.
- **CRITICAL**: If the user accidentally shares sensitive info (e.g. OTP, PIN, passwords, account numbers, etc.), do NOT repeat or store it. Inform them immediately:
  "For your security, please don't share OTPs, PINs, passwords or banking credentials with me."
- Never promise or guarantee scheme approval, loan disbursement, or financial payouts.
- If the lookup tool returns success=false with NOT_FOUND error, say:
  "I don't currently have verified information about that scheme in my available government-scheme data, so I don't want to guess."
- If the lookup tool returns success=false with FIELD_NOT_AVAILABLE, say:
  "I don't currently have verified information for that specific aspect of the scheme in my current dataset, so I don't want to guess."
- If the lookup tool fails due to TIMEOUT or CONNECTION_ERROR, say:
  "I'm unable to reach the government information source right now. I don't want to guess or provide outdated information. Please try again shortly."

# LANGUAGE & SCRIPTS
- Always respond in the user's current/detected language.
- Supported languages: English, Hindi, Tamil, Telugu.
- Always write non-English languages using their correct native script:
  - English -> Latin script
  - Hindi -> Devanagari script (e.g. "प्रधानमंत्री मुद्रा योजना के बारे में...") - NEVER Romanized.
  - Tamil -> Tamil script (e.g. "இந்தத் திட்டத்தைப் பற்றி...") - NEVER Romanized.
  - Telugu -> Telugu script (e.g. "ఈ పథకం గురించి...") - NEVER Romanized.
- The user's input may be code-mixed or Romanized (e.g., "PMMY ke baare mein batao", "PMJDY pathi sollunga"). Understand it naturally, but respond in the correct native script. Never simply mirror Romanized Indian languages.

# OUT-OF-ROLE TOPICS
If the user changes topic to something outside your role (such as general financial literacy, digital payment safety, budgeting, savings, compound interest, or cyber fraud/scams), or explicitly asks to connect/talk to the assistant, you MUST call the `return_to_main_agent` tool immediately. Do not try to answer these yourself.
If you cannot call it, politely say:
"I specialize in government schemes. For that question, FinBuddy's general financial assistant may be better suited."
Do NOT hand off back or loop. Just state this response.
"""

class GovernmentSchemeSpecialist(Agent):
    def __init__(self, main_assistant, user_id: str = "default_user", language: str = "English", scheme_name: str = None, user_query: str = None) -> None:
        self.main_assistant = main_assistant
        self.user_id = user_id
        self.language = language
        self.scheme_name = scheme_name
        self.user_query = user_query
        
        # Inject dynamic context parameters to prompt to greet user and answer immediately without asking
        instructions = SPECIALIST_SYSTEM_PROMPT
        if scheme_name:
            instructions += f"\n\n# ACTIVE CONTEXT\n- Scheme mentioned by user: {scheme_name}\n"
        if user_query:
            instructions += f"- Original User Query: {user_query}\n"
        if language:
            instructions += f"- Detected Language: {language}\n"
            
        instructions += f"\n- Current User ID: {user_id}\n"
        
        # Specialist introduction requirements
        intro_dict = {
            "Hindi": f"नमस्ते, मैं फिनबड्डी का सरकारी योजना विशेषज्ञ हूँ। मैं पात्रता, लाभ, दस्तावेजों और आवेदन की जानकारी में आपकी मदद कर सकता हूँ। मैं समझता हूँ कि आप {scheme_name or ''} के बारे में पूछ रहे हैं। चलिए मैं इसमें आपकी मदद करता हूँ।",
            "Tamil": f"வணக்கம், நான் பின்படியின் அரசு திட்ட நிபுணர். தகுதி, நன்மைகள், ஆவணங்கள் மற்றும் விண்ணப்பத் தகவல்களுக்கு நான் உங்களுக்கு உதவ முடியும். நீங்கள் {scheme_name or ''} பற்றி கேட்கிறீர்கள் என்று எனக்குப் புரிகிறது. அதற்கு நான் உதவுகிறேன்.",
            "Telugu": f"నమస్కారం, నేను ఫిన్‌బడ్డీ ప్రభుత్వ పథకాల నిపుణుడిని. అర్హత, ప్రయోజనాలు, పత్రాలు మరియు దరఖాస్తు సమాచారంతో నేను సహాయం చేయగలను. మీరు {scheme_name or ''} గురించి అడుగుతున్నారని నేను గ్రహించాను. దానికి నేను సహాయం చేస్తాను.",
            "English": f"Hello, I'm FinBuddy's government scheme specialist. I can help you with eligibility, benefits, documents and application information. I understand you're asking about {scheme_name or ''}. Let me help with that."
        }
        greeting = intro_dict.get(language, intro_dict["English"])
        instructions += f"\n\n# FIRST-TURN GREETING\nYou must welcome the user and answer the original query immediately. Greet them EXACTLY with this greeting:\n\"{greeting}\"\n"
        
        super().__init__(instructions=instructions)

    @function_tool
    async def return_to_main_agent(
        self,
        user_query: str,
        intent: str,
        language: str
    ) -> str:
        """Return the conversation back to FinBuddy's main general financial assistant when the user asks a question outside government schemes (such as general financial concepts, budgeting, savings, safety, compound interest, banking, digital payments) or when the user reports cyber fraud/scams, or explicitly asks to talk to the general assistant.
        
        Args:
            user_query: The user's query that is outside government schemes.
            intent: The detected intent category (e.g. CYBER_FRAUD, GENERAL).
            language: The user's preferred language.
        """
        logger.info(f"GovernmentSchemeSpecialist: Returning to main agent. Query: {user_query}, Intent: {intent}")
        
        # Inject the query and intent to main assistant context so it triggers the routing instantly on enter
        if intent == "CYBER_FRAUD":
            announcement = "Understood. This is better handled by our cyber fraud and financial safety specialist. I'll connect you now."
            intro_dict = {
                "Hindi": "मैं समझता हूँ। यह हमारे साइबर धोखाधड़ी और वित्तीय सुरक्षा विशेषज्ञ द्वारा बेहतर ढंग से संभाला जा सकता है। मैं आपको अभी जोड़ता हूँ।",
                "Tamil": "புரிந்துகொண்டேன். இதை எங்கள் சைபர் மோசடி மற்றும் நிதி பாதுகாப்பு நிபுணர் சிறப்பாகக் கையாள முடியும். நான் உங்களை இப்போது இணைக்கிறேன்.",
                "Telugu": "అర్థమైంది. ఇది మా సైబర్ మోసాలు మరియు ఆర్థిక భద్రత నిపుణుడి ద్వారా మెరుగ్గా నిర్వహించబడుతుంది. నేను మిమ్మల్ని ఇప్పుడు కనెక్ట్ చేస్తాను."
            }
            announcement = intro_dict.get(language, announcement)
            
            # Since the layout requires: Government Specialist -> Main Agent -> Cyber Fraud Specialist
            # Let's perform the update to main agent, and instruct it to call handoff immediately or we can directly let the main assistant call the tool.
            # To make it seamless, when self.main_assistant is updated as the active agent, we want it to run its next turn.
            # We can update self.main_assistant's instructions/state so that on next turn it knows the queued query.
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
        logger.info(f"Specialist: Looking up caller with user_id: {user_id}")
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
        logger.info(f"Specialist: Saving caller details for {user_id} - {name}")
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
        logger.info(f"Specialist: create_escalation tool called for user {user_id}")
        
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

    @function_tool
    async def lookup_government_scheme(
        self,
        scheme_name: str,
        information_requested: str,
    ) -> str:
        """Use this tool whenever the user asks about a specific Indian government financial scheme, including: overview, eligibility, benefits, premiums, loan categories, application process, required documents, or current/latest status.
        
        Args:
            scheme_name: The name, abbreviation, or alias of the government scheme.
            information_requested: The specific aspect requested (e.g. 'overview', 'eligibility', 'benefits', 'application', 'documents', 'latest_status').
        """
        logger.info(f"Specialist: lookup_government_scheme called: scheme={scheme_name}, info={information_requested}")
        
        # Defer to main assistant to reuse lookup db logic and call outcome success checking
        return await self.main_assistant.lookup_government_scheme(
            scheme_name=scheme_name,
            information_requested=information_requested
        )
