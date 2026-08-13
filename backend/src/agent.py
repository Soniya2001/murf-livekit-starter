import logging
import json
import asyncio
import re
from datetime import datetime
import uuid

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
    UserInputTranscribedEvent,
    SpeechCreatedEvent,
    function_tool,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from db import get_caller, save_caller, create_escalation
from schemes_data import lookup_scheme_db

logger = logging.getLogger("agent")

load_dotenv(".env.local")

SYSTEM_PROMPT = """
# IDENTITY
You are a friendly, professional, and empathetic Financial Services Assistant working for the Financial Services Literacy Initiative. Your role is to help users understand government financial schemes, improve banking and financial literacy, and raise awareness about online scams and frauds.

# FIRST-TURN GREETING
Greet the user immediately and warmly:
"Hello! I am your Financial Services Assistant. How can I help you learn about financial schemes, banking, or staying safe from fraud today?"

# OBJECTIVES
- Educate users on various government financial schemes (pension, insurance, and subsidies).
- Improve general banking and financial literacy (savings, budgeting, digital payments).
- Raise awareness about common financial frauds and online scams, providing actionable security advice.

# KNOWLEDGE & TOOL CALLS
- Do NOT answer specific details about government financial schemes (such as eligibility criteria, benefits, premiums, application processes, or required documents) from memory or from the user profile.
- You MUST call the `lookup_government_scheme` tool whenever the user asks for information about a specific government financial scheme (e.g. PMJDY, APY, PMJJBY, PMSBY, PMMY / PM Mudra, Stand-Up India, JanSamarth), even if the scheme is mentioned in the RETURNING USER PROFILE.
- When explaining the retrieved information, tell the user the official source and source update date. Say: "According to information sourced from the official government portal [source], last updated on [source_updated_at]..." Keep it clean and easy to say. Do NOT refer to retrieved_at as the time the official government website was accessed.
- Summarize long text naturally for a spoken conversation. Do not read raw lists or complex tables.
- Knowledge stops at: Personal account details, transaction processing, and making final approvals or commitments on behalf of any institution.

# HUMAN HELP ESCALATION & CONSENT
- Use `create_escalation` ONLY when:
  1. The caller explicitly asks to speak with a human/support team.
  2. The caller reports a suspected financial scam, fraud, or possible unauthorized activity.
  3. The caller needs account-specific assistance that you cannot access (like check account status).
  4. The caller needs an action that you are not authorized to perform.
  5. The caller's issue cannot be safely resolved with available scheme info.
  6. The caller needs institutional support from a bank.
- Do NOT call it for:
  1. Normal financial-literacy questions (e.g., general definitions).
  2. Basic government-scheme explanations.
  3. Questions you can answer safely.
- **CRITICAL - CONSENT BEFORE ESCALATION**: You must obtain explicit user consent before calling `create_escalation`. Tell the user:
  1. Why human help may be useful.
  2. What information will be shared (e.g., caller name, summary, urgency, language, preferred contact method).
  3. Reassure them that you won't share sensitive credentials (OTP, PIN, password, account number).
  4. Ask if they want you to create the request and ask for their preferred contact method (phone or email).
  Example consent script: "I can create a request for human assistance. I would share a short summary of what happened, what I have already checked, your preferred language, and how you'd like to be contacted. I won't share your OTP, PIN, password, account number, or other sensitive banking information. Would you like me to create the request?"
  - Speak this consent request in the user's current/detected language.
  - If the user refuses (says "no", "don't", "not now", "I don't want that"), do NOT call `create_escalation`. Respond with: "Understood. I won't create a human-help request. I can still help with general financial information." (or translated equivalent).
  - Only when they agree and provide preferred follow-up method (phone or email), call `create_escalation`.
  - Once created, state: "Your request has been created with reference ID FIN-XXXX (read the actual returned reference ID). It is currently marked as [urgency] priority. A human support process can review the request according to the available support workflow. You've selected [follow-up method] as your preferred follow-up method. I can't guarantee an immediate response."

# LANGUAGE & SCRIPTS
- Always detect the user's current language and respond in the same language unless the user explicitly asks for another language.
- Always write non-English languages using their correct native script:
  - English -> Latin script (e.g., "How can I help you?")
  - Hindi -> Devanagari script (e.g., "नमस्ते, मैं आपकी कैसे मदद कर सकता हूँ?") - NEVER write Hindi in Romanized script (e.g. "Namaste, main aapki kaise...").
  - Tamil -> Tamil script (e.g., "வணக்கம், நான் உங்களுக்கு எப்படி உதவலாம்?") - NEVER write Tamil in Romanized script (e.g. "Vanakkam, naan ungalukku...").
  - Telugu -> Telugu script (e.g., "నమస్కారం, నేను మీకు ఎలా సహాయం చేయవచ్చు?") - NEVER write Telugu in Romanized script (e.g. "Namaskaram, nenu meeku...").
- The user's speech may be code-mixed or Romanized (e.g. "PMJDY pathi sollunga", "PMMY ke baare mein batao"). Understand these naturally, but respond in the appropriate native script.
- For code-mixed conversations, preserve commonly used English technical/financial terms when natural (e.g., "UPI payment", "OTP", "bank account"), but keep the surrounding Indian language in its native script.
- If the user explicitly asks you to speak in a specific language (e.g., "Speak in English", "தமிழில் பேசுங்கள்", "हिंदी में बात करें", "తెలుగులో మాట్లాడండి"), you must follow that instruction and continue in that language.

# GUARDRAILS
- **CRITICAL**: Never ask for or accept an OTP (One-Time Password), PIN, password, bank account number, CVV, Aadhaar, or PAN.
- **CRITICAL**: If the user accidentally shares sensitive info (e.g., "my account number is 123456" or "my OTP is 123"), warn them immediately: "For your security, please do not share OTPs, PINs, passwords, or banking credentials with me." Do NOT repeat or store this information anywhere!
- **CRITICAL**: Never promise or guarantee scheme approval, loan disbursement, or financial payouts.
- **CRITICAL**: If the lookup tool returns success=false with NOT_FOUND error, say: "I don't currently have verified information about that scheme in my government-scheme dataset, so I don't want to guess. You can check the relevant official government portal for the latest information." Do NOT say: "I checked the government source and it doesn't exist."
- **CRITICAL**: If the lookup tool returns success=false with FIELD_NOT_AVAILABLE, say: "I don't currently have verified information for that specific aspect of the scheme in my current dataset, so I don't want to guess. Please check the relevant official government portal."
- **CRITICAL**: If the lookup tool fails due to TIMEOUT or CONNECTION_ERROR, say: "I'm unable to reach the government information source right now. I don't want to guess or provide outdated information. Please try again shortly."
- **CRITICAL**: Never claim: "You are approved." Instead, say: "Based on the information available, you may meet the published criteria, but final eligibility is determined by the relevant authority."
- **Escalation Script / Refusal**: If a user asks about account-specific actions, transaction processing, or demands approvals, say: "For your security, I cannot ask for or process OTPs, PINs, or account details, and I cannot guarantee scheme approvals. Please contact your official bank branch directly for assistance with your account."

# MEMORY & CONSENT GUARDRAILS
- **CRITICAL**: You MUST ask the caller for permission before saving or remembering any information. For example, say: "Would it be alright if I remember your name and the schemes we discussed for next time?"
- If the caller says NO, do NOT save their information and do NOT call the save tool.
- If the caller says YES, call the `save_caller_details` tool to store their name, language, and eligibility/checked schemes facts.
- Facts to save: Schemes already checked (e.g. APY, PMJJBY, PMSBY, PMMY), eligibility answers. Do NOT store account or ID numbers.

# STYLE
- Keep responses short and conversational, suitable for a spoken voice assistant.
- Use simple punctuation; avoid bullet lists with complex symbols or emojis that are hard to speak.
- Maintain a comfortable conversational pace.
- If the user is silent, gently check in: "Are you still there? Let me know how I can help."

# OPT-OUT / STOP CALL GUARDRAIL
If the user expresses a desire to stop, end, or opt out of the call (using phrases like "stop", "don't call me", "end the call", "I don't want this", "goodbye", "remove me", or any translated equivalent), you MUST immediately respond with:
"Understood. I won't continue this call and will make sure you are not contacted again. Thank you, and have a good day."
Do NOT ask any follow-up questions, do NOT try to convince them, and do NOT continue the conversation.
"""


def num_to_tamil(num: int) -> str:
    if num == 0:
        return "பூஜ்ஜியம்"
        
    ones = {
        1: "ஒன்று", 2: "இரண்டு", 3: "மூன்று", 4: "நான்கு", 5: "ஐந்து",
        6: "ஆறு", 7: "ஏழு", 8: "எட்டு", 9: "ஒன்பது"
    }
    
    def convert_999(n):
        if n == 0:
            return ""
        parts = []
        
        # Hundreds
        hundreds = n // 100
        rem = n % 100
        if hundreds > 0:
            hundreds_names = {
                1: "நூறு", 2: "இருநூறு", 3: "முந்நூறு", 4: "நானூறு", 5: "ஐந்நூறு",
                6: "அறுநூறு", 7: "எழுநூறு", 8: "எண்ணூறு", 9: "தொள்ளாயிரம்"
            }
            hundreds_prefixes = {
                1: "நூற்று", 2: "இருநூற்று", 3: "முந்நூற்று", 4: "நானூற்று", 5: "ஐந்நூற்று",
                6: "அறுநூற்று", 7: "எழுநூற்று", 8: "எண்ணூற்று", 9: "தொள்ளாயிரத்து"
            }
            if rem > 0:
                parts.append(hundreds_prefixes[hundreds])
            else:
                parts.append(hundreds_names[hundreds])
                
        # Tens and ones
        if rem > 0:
            if rem < 10:
                parts.append(ones[rem])
            elif rem == 10:
                parts.append("பத்து")
            elif rem < 20:
                teens = {
                    11: "பதினொன்று", 12: "பன்னிரண்டு", 13: "பதின்மூன்று", 14: "பதினான்கு",
                    15: "பதினைந்து", 16: "பதினாறு", 17: "பதினேழு", 18: "பதினெட்டு", 19: "பத்தொன்பது"
                }
                parts.append(teens[rem])
            else:
                tens = rem // 10
                o = rem % 10
                tens_names = {
                    2: "இருபது", 3: "முப்பது", 4: "நாற்பது", 5: "ஐம்பது",
                    6: "அறுபது", 7: "எழுபது", 8: "எண்பது", 9: "தொண்ணூறு"
                }
                tens_prefixes = {
                    2: "இருபத்து", 3: "முப்பத்து", 4: "நாற்பத்து", 5: "ஐம்பத்து",
                    6: "அறுபத்து", 7: "எழுபத்து", 8: "எண்பத்து", 9: "தொண்ணூற்று"
                }
                if o > 0:
                    parts.append(tens_prefixes[tens] + ones[o])
                else:
                    parts.append(tens_names[tens])
        return "".join(parts)

    def convert_large(n):
        if n == 0:
            return ""
        if n < 1000:
            return convert_999(n)
            
        # Crores
        if n >= 10000000:
            crores = n // 10000000
            rem = n % 10000000
            c_part = "ஒரு கோடி" if crores == 1 else convert_large(crores) + " கோடி"
            if rem > 0:
                c_part = c_part.replace("கோடி", "கோடியே")
                return c_part + convert_large(rem)
            return c_part
            
        # Lakhs
        if n >= 100000:
            lakhs = n // 100000
            rem = n % 100000
            l_part = "ஒரு லட்சம்" if lakhs == 1 else convert_large(lakhs) + " லட்சம்"
            if rem > 0:
                l_part = l_part.replace("லட்சம்", "லட்சத்து")
                return l_part + convert_large(rem)
            return l_part
            
        # Thousands
        thousands = n // 1000
        rem = n % 1000
        
        t_prefix = ""
        if thousands == 1:
            t_prefix = "ஆயிரத்து" if rem > 0 else "ஆயிரம்"
        else:
            t_base = convert_large(thousands)
            if t_base.endswith("ஒன்று"):
                t_prefix = t_base[:-5] + ("ஓராயிரத்து" if rem > 0 else "ஓராயிரம்")
            elif t_base.endswith("இரண்டு"):
                t_prefix = t_base[:-6] + ("இரண்டாயிரத்து" if rem > 0 else "இரண்டாயிரம்")
            elif t_base.endswith("மூன்று"):
                t_prefix = t_base[:-6] + ("மூன்றாயிரத்து" if rem > 0 else "மூன்றாயிரம்")
            elif t_base.endswith("நான்கு"):
                t_prefix = t_base[:-6] + ("நான்காயிரத்து" if rem > 0 else "நான்காயிரம்")
            elif t_base.endswith("ஐந்து"):
                t_prefix = t_base[:-5] + ("ஐந்தாயிரத்து" if rem > 0 else "ஐந்தாயிரம்")
            elif t_base.endswith("ஆறு"):
                t_prefix = t_base[:-3] + ("ஆறாயிரத்து" if rem > 0 else "ஆறாயிரம்")
            elif t_base.endswith("ஏழு"):
                t_prefix = t_base[:-3] + ("ஏழாயிரத்து" if rem > 0 else "ஏழாயிரம்")
            elif t_base.endswith("எட்டு"):
                t_prefix = t_base[:-4] + ("எட்டாயிரத்து" if rem > 0 else "எட்டாயிரம்")
            elif t_base.endswith("ஒன்பது"):
                t_prefix = t_base[:-6] + ("ஒன்பதாயிரத்து" if rem > 0 else "ஒன்பதாயிரம்")
            elif t_base.endswith("பத்து"):
                t_prefix = t_base[:-5] + ("பத்தாயிரத்து" if rem > 0 else "பத்தாயிரம்")
            elif t_base.endswith("இருபது"):
                t_prefix = t_base[:-6] + ("இருபதாயிரத்து" if rem > 0 else "இருபதாயிரம்")
            elif t_base.endswith("முப்பது"):
                t_prefix = t_base[:-7] + ("முப்பதாயிரத்து" if rem > 0 else "முப்பதாயிரம்")
            elif t_base.endswith("நாற்பது"):
                t_prefix = t_base[:-7] + ("நாற்பதாயிரத்து" if rem > 0 else "நாற்பதாயிரம்")
            elif t_base.endswith("ஐம்பது"):
                t_prefix = t_base[:-6] + ("ஐம்பதாயிரத்து" if rem > 0 else "ஐம்பதாயிரம்")
            elif t_base.endswith("அறுபது"):
                t_prefix = t_base[:-6] + ("அறுபதாயிரத்து" if rem > 0 else "அறுபதாயிரம்")
            elif t_base.endswith("எழுபது"):
                t_prefix = t_base[:-6] + ("எழுபதாயிரத்து" if rem > 0 else "எழுபதாயிரம்")
            elif t_base.endswith("எண்பது"):
                t_prefix = t_base[:-6] + ("எண்பதாயிரத்து" if rem > 0 else "எண்பதாயிரம்")
            elif t_base.endswith("தொண்ணூறு"):
                t_prefix = t_base[:-8] + ("தொண்ணூறாயிரத்து" if rem > 0 else "தொண்ணூறாயிரம்")
            else:
                t_prefix = t_base + (" ஆயிரத்து" if rem > 0 else " ஆயிரம்")
                
        return t_prefix + convert_large(rem)

    return convert_large(num)


def replace_numbers_with_tamil(text: str) -> str:
    def repl(match):
        num_str = match.group(0).replace(",", "")
        try:
            val = int(num_str)
            return num_to_tamil(val)
        except Exception:
            return match.group(0)
    return re.sub(r'\b\d+(?:,\d+)*\b', repl, text)


class TamilNumberFriendlyTTS(murf.TTS):
    def __init__(self, *args, **kwargs):
        self.assistant_ref = None
        super().__init__(*args, **kwargs)

    def synthesize(self, text: str, *args, **kwargs):
        if self.assistant_ref and getattr(self.assistant_ref, "language", "") == "Tamil":
            try:
                text = replace_numbers_with_tamil(text)
            except Exception as e:
                logger.error(f"Error converting numbers to Tamil: {e}")
        return super().synthesize(text, *args, **kwargs)


class Assistant(Agent):
    def __init__(self, user_id: str = "default_user", initial_info: str = "", is_sip: bool = False) -> None:
        instructions = SYSTEM_PROMPT
        
        if is_sip:
            greeting = "Hello, this is FinBuddy, an AI financial information assistant. I'm calling to inform you about newly launched and updated government financial schemes, including the Pradhan Mantri MUDRA Yojana. To stop this call and make sure you are not contacted again, please tell 1. To continue this call and hear about the schemes, please tell 2."
            if initial_info:
                try:
                    caller_data = json.loads(initial_info)
                    name = caller_data.get("name")
                    if name:
                        greeting = f"Hello {name}, this is FinBuddy, an AI financial information assistant. I'm calling to inform you about newly launched and updated government financial schemes, including the Pradhan Mantri MUDRA Yojana. To stop this call and make sure you are not contacted again, please tell 1. To continue this call and hear about the schemes, please tell 2."
                except Exception:
                    pass
            instructions = instructions.replace(
                'Greet the user immediately and warmly:\n"Hello! I am your Financial Services Assistant. How can I help you learn about financial schemes, banking, or staying safe from fraud today?"',
                f'You must greet the user immediately with this exact greeting:\n"{greeting}"'
            )
            instructions += "\n\n# OUTBOUND CALL ENVIRONMENT\n- This is an unsolicited outbound call. You must respect the user's consent and opt-out requests instantly. Never ask for or mention sensitive details like OTP, PIN, password, bank account, Aadhaar, PAN, card numbers, or credentials."
        else:
            # If returning user info is present, inject greeting instruction
            if initial_info:
                try:
                    caller_data = json.loads(initial_info)
                    name = caller_data.get("name", "there")
                    facts = caller_data.get("facts", {})
                    schemes = facts.get("schemes_checked", "N/A")
                    instructions = instructions.replace(
                        'Greet the user immediately and warmly:\n"Hello! I am your Financial Services Assistant. How can I help you learn about financial schemes, banking, or staying safe from fraud today?"',
                        f'Greet the user back by name, welcome them back, and continue from last time. For example: "Hello {name}, welcome back! Last time we spoke about {schemes}. How are you doing with that or did it help?"'
                    )
                    instructions += f"\n\n# RETURNING USER PROFILE\n{initial_info}\n"
                except Exception:
                    pass
                
        instructions += f"\n\n# CURRENT SESSION INFO\n- Current User ID: {user_id}\n"
        super().__init__(instructions=instructions)
        
        # Day 8 call outcome state tracking
        self.call_id = None
        self.call_goal_completed = False
        self.success_reason = None
        self.scheme_name = None
        self.information_requested = None
        self.language = "English"
        
        # Buffer properties for success state until playout completes
        self.pending_success = False
        self.pending_success_reason = None
        self.pending_scheme_name = None
        self.pending_information_requested = None

    def mark_call_success(self, success_reason: str, scheme_name: str = None, information_requested: str = None):
        """Internal helper to mark the call as successful once conditions are met."""
        if self.call_id and self.call_id.startswith("call-"):
            self.call_goal_completed = True
            self.success_reason = success_reason
            self.scheme_name = scheme_name
            self.information_requested = information_requested
        else:
            self.pending_success = True
            self.pending_success_reason = success_reason
            self.pending_scheme_name = scheme_name
            self.pending_information_requested = information_requested


    @function_tool
    async def lookup_caller(self, user_id: str) -> str:
        """Look up details of a caller by user_id to see their name, language preference, and history.
        
        Args:
            user_id: The unique identifier/phone number of the caller.
        """
        logger.info(f"Looking up caller with user_id: {user_id}")
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
        logger.info(f"Saving caller details for {user_id} - {name}")
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
        
        Use this tool when:
        - The caller explicitly asks to speak with a human.
        - The caller reports a suspected financial scam or fraud.
        - The caller needs account-specific assistance that FinBuddy cannot provide.
        - The caller needs an action that FinBuddy is not authorized to perform.
        - The caller's issue cannot be safely resolved with available government-scheme information.
        - The caller needs institutional support from a bank or authorized financial service provider.
        
        Do NOT call this for:
        - Normal financial-literacy questions.
        - Basic government-scheme explanations.
        - Questions that FinBuddy can answer safely.
        - General information requests.
        
        CRITICAL: NEVER create an escalation request without obtaining explicit user consent first.
        
        Args:
            user_id: The unique identifier/phone number of the caller.
            issue_summary: A short summary of the issue (e.g. Suspected fraudulent UPI transaction).
            what_happened: A description of what happened. Do NOT include sensitive info like OTP, PIN, passwords, account numbers, card credentials, Aadhaar, or PAN.
            agent_checks: What the agent checked or provided (e.g. Provided general scam-safety guidance).
            urgency: The urgency level of the request. Must be 'low', 'medium', or 'high'.
            language: The language the user prefers (e.g. Tamil, Telugu, Hindi, English).
            preferred_follow_up: Preferred contact channel ('phone' or 'email').
            caller_name: Optional name of the caller if known or provided.
        """
        logger.info(f"create_escalation tool called for user {user_id}")
        
        # 1. Input Validation
        urgency = (urgency or "low").lower()
        if urgency not in ["low", "medium", "high"]:
            urgency = "low"
            
        preferred_follow_up = (preferred_follow_up or "phone").lower()
        if preferred_follow_up not in ["phone", "email"]:
            preferred_follow_up = "phone"
            
        # 2. Remove/Reject Sensitive Information
        sensitive_pattern = re.compile(
            r'\b(\d{4,6})\b|\b(\d{9,18})\b|otp|pin|password|cvv|aadhaar|pan|card number',
            re.IGNORECASE
        )
        
        # Helper to scrub sensitive information
        def scrub(text):
            if not text:
                return ""
            # Simple scrub of potential account numbers (9-18 digits) or PIN/OTP (4-6 digits)
            text = re.sub(r'\b\d{9,18}\b', '[SCRUBBED ACCOUNT/CARD]', text)
            text = re.sub(r'\b\d{4,6}\b', '[SCRUBBED CREDENTIAL]', text)
            # Scrub keywords
            for word in ["otp", "pin", "password", "cvv", "aadhaar", "pan"]:
                text = re.sub(rf'\b{word}\b\s*\S*', '[SCRUBBED SENSITIVE]', text, flags=re.IGNORECASE)
            return text

        issue_summary = scrub(issue_summary)
        what_happened = scrub(what_happened)
        agent_checks = scrub(agent_checks)
        
        # Try to resolve caller name from db if not explicitly provided
        if not caller_name:
            caller = get_caller(user_id)
            if caller:
                caller_name = caller.get("name")
        if not caller_name:
            caller_name = "Anonymous Caller"

        # 3. Generate a unique reference ID in format FIN-YYYYMMDD-XXXX
        today = datetime.now().strftime("%Y%m%d")
        random_suffix = str(uuid.uuid4().int)[:4]
        reference_id = f"FIN-{today}-{random_suffix}"
        
        # 4. Save the request to SQLite
        res = create_escalation(
            user_id=user_id,
            reference_id=reference_id,
            caller_name=caller_name,
            issue_summary=issue_summary,
            what_happened=what_happened,
            agent_checks=agent_checks,
            urgency=urgency,
            language=language,
            preferred_follow_up=preferred_follow_up,
            status="OPEN"
        )
        
        if res.get("success"):
            return json.dumps({
                "success": True,
                "reference_id": reference_id,
                "status": "OPEN"
            })
        else:
            return json.dumps({
                "success": False,
                "error": res.get("error", "Failed to save request")
            })

    @function_tool
    async def lookup_government_scheme(
        self,
        scheme_name: str,
        information_requested: str,
    ) -> str:
        """Use this tool whenever the user asks about a specific Indian government financial scheme, including: overview, eligibility, benefits, premiums, loan categories, application process, required documents, or current/latest status.
        
        Use this tool instead of relying on LLM memory. If the scheme cannot be found, the tool returns NOT_FOUND. If information is not available, the tool returns FIELD_NOT_AVAILABLE. Do not invent answers. If the user asks a general financial-literacy question that does not refer to a specific government scheme, do not call this tool.
        
        Args:
            scheme_name: The name, abbreviation, or alias of the government scheme (e.g., 'PMJDY', 'APY', 'PMJJBY', 'PMSBY', 'PMMY', 'PM Mudra', 'Mudra loan', 'Stand-Up India', 'JanSamarth').
            information_requested: The specific aspect requested (e.g. 'overview', 'eligibility', 'benefits', 'application', 'documents', 'latest_status').
        """
        logger.info(f"lookup_government_scheme called: scheme={scheme_name}, info={information_requested}")
        
        # Financial safety: Block if user query requests OTP, PIN, password, or account check
        sensitive_keywords = ["otp", "pin", "password", "cvv", "aadhaar", "pan", "account number", "card number"]
        if any(kw in scheme_name.lower() or kw in information_requested.lower() for kw in sensitive_keywords):
            logger.warning("Blocked sensitive credentials lookup via tool.")
            return json.dumps({
                "success": False,
                "error_type": "SECURITY_REFUSAL",
                "message": "Sensitive credentials checks are prohibited."
            })

        try:
            # Enforce 8-second HTTP timeout equivalent for external source simulation
            result = await asyncio.wait_for(
                lookup_scheme_db(scheme_name, information_requested),
                timeout=8.0
            )
            logger.info(f"lookup_government_scheme result: {result.get('success')}")
            if result.get("success"):
                info_type = result.get("info_type")
                if info_type == "documents":
                    self.mark_call_success("Document list provided", scheme_name, information_requested)
                elif info_type == "eligibility":
                    self.mark_call_success("Eligibility check completed", scheme_name, information_requested)
            return json.dumps(result)
        except asyncio.TimeoutError:
            logger.error("lookup_government_scheme timed out")
            return json.dumps({
                "success": False,
                "error_type": "TIMEOUT",
                "message": "Government data source timed out."
            })
        except Exception as e:
            logger.error(f"lookup_government_scheme error: {e}")
            return json.dumps({
                "success": False,
                "error_type": "CONNECTION_ERROR",
                "message": f"Connection error or API unavailable: {str(e)}"
            })



server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Look up user if they already exist
    user_id = "default_user"
    initial_info = ""
    is_sip = ctx.room.name.startswith("sip_room_")
    caller_profile = None
    try:
        import asyncio
        remote_participant = None
        for _ in range(50):
            if ctx.room.remote_participants:
                remote_participant = next(iter(ctx.room.remote_participants.values()))
                break
            await asyncio.sleep(0.1)

        if remote_participant:
            user_id = remote_participant.identity
            caller_profile = get_caller(user_id)
            if caller_profile:
                initial_info = json.dumps(caller_profile)
    except Exception as e:
        logger.error(f"Error during initial caller lookup: {e}")

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3",language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=TamilNumberFriendlyTTS(
                voice="Anisha", 
                locale="en-IN",
                style="Conversational",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    @session.on("speech_created")
    def on_speech_created(ev: SpeechCreatedEvent):
        speech_handle = ev.speech_handle
        
        def on_done(fut):
            if not speech_handle.interrupted or ctx.room.isconnected():
                if getattr(assistant, "pending_success", False):
                    assistant.call_goal_completed = True
                    assistant.success_reason = assistant.pending_success_reason
                    assistant.scheme_name = assistant.pending_scheme_name
                    assistant.information_requested = assistant.pending_information_requested
                    assistant.pending_success = False
                    logger.info("Speech playout completed successfully. Call marked as SUCCESS.")
        
        speech_handle._done_fut.add_done_callback(on_done)

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.transcript.strip().lower()
        if not transcript:
            return

        if is_sip:
            opt_out_phrases = ["stop", "don't call me", "dont call me", "end the call", "i don't want this", "i dont want this", "goodbye", "remove me", "one", "1"]
            continue_phrases = ["two", "2"]
            if any(phrase in transcript for phrase in opt_out_phrases):
                logger.info(f"Opt-out detected in transcription: '{transcript}'. Shutting down call...")
                async def shutdown():
                    try:
                        session.interrupt()
                        session.clear_user_turn()
                        await session.say("Understood. I won't continue this call and will make sure you are not contacted again. Thank you, and have a good day.", allow_interruptions=False)
                        await asyncio.sleep(5.0)
                    except Exception as e:
                        logger.error(f"Error during opt-out greeting: {e}")
                    finally:
                        logger.info("Disconnecting room due to user opt-out.")
                        await ctx.room.disconnect()
                asyncio.create_task(shutdown())
                ev.transcript = ""
                return
            elif any(phrase in transcript for phrase in continue_phrases):
                logger.info(f"Continue detected in transcription: '{transcript}'. Prompting user...")
                async def continue_call():
                    try:
                        session.interrupt()
                        session.clear_user_turn()
                        await session.say("Great! Let's continue. I can explain Indian government financial schemes such as PMJDY, APY, PMSBY, PMJJBY, and PM MUDRA Yojana. What would you like to learn about?", allow_interruptions=True)
                    except Exception as e:
                        logger.error(f"Error during continue: {e}")
                asyncio.create_task(continue_call())
                ev.transcript = ""
                return

        # Check for Devanagari script characters (native Hindi)
        has_devanagari = any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in transcript)

        # Check for Tamil script characters (native Tamil)
        has_tamil = any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in transcript)

        # Check for Telugu script characters (native Telugu)
        has_telugu = any(ord(c) >= 0x0C00 and ord(c) <= 0x0C7F for c in transcript)

        # Check for common Hinglish/Hindi romanized keywords
        hindi_keywords = {
            "kya", "hai", "aur", "haan", "nahin", "aap", "namaste", "shukriya",
            "batao", "bataiye", "samjhao", "dhan", "suraksha",
            "raha", "rahi", "rha", "rhi", "mujhe", "mera", "meri", "hum", "tum", "apna", "apni",
            "karke", "karo", "karna"
        }

        # Check for common Tanglish/Tamil romanized keywords
        tamil_keywords = {
            "vanakkam", "nandri", "aama", "illa", "enaku", "ungalukku", "theriyum", "theriyathu",
            "panna", "pannunga", "solla", "sollunga", "keta", "kelunga", "kaasu",
            "vangi", "semipu", "kadan", "thittam",
            "naan", "neenga", "avanga", "ivan", "iru", "iruku", "irukanga", "yen", "eppadi",
            "eppo", "enga", "enna", "romba", "nalla", "veedu", "kaala", "nalla-irukingala"
        }

        # Check for common Telugu/Telish romanized keywords
        telugu_keywords = {
            "namaskaram", "dhanyavadalu", "avunu", "kadu", "naku", "meeku", "telusu", "teliyadu",
            "cheyandi", "cheyyali", "cheppandi", "dhanam", "vaddi",
            "pathakam", "nenu", "meeru", "varu", "vadu", "ela",
            "eppudu", "ekkada", "enti", "chala", "bagundi", "illu", "kalam"
        }

        words = set(transcript.split())

        # Check detected language from STT event
        detected_lang = (getattr(ev, "language", "") or "").lower()

        # Handle explicit override requests
        if "speak in english" in transcript:
            logger.info("Manual override to English detected.")
            session.tts.update_options(voice="Anisha", locale="en-IN", style="Conversation")
            assistant.language = "English"
        elif "தமிழில் பேசுங்கள்" in transcript or "tamilil pesungal" in transcript or "speak in tamil" in transcript:
            logger.info("Manual override to Tamil detected.")
            session.tts.update_options(voice="Karthikeyan", locale="ta-IN", style="Conversational")
            assistant.language = "Tamil"
        elif "हिंदी में बात करें" in transcript or "hindi mein baat karen" in transcript or "speak in hindi" in transcript:
            logger.info("Manual override to Hindi detected.")
            session.tts.update_options(voice="Anisha", locale="hi-IN", style="Conversation")
            assistant.language = "Hindi"
        elif "తెలుగులో మాట్లాడండి" in transcript or "telugulo matladandi" in transcript or "speak in telugu" in transcript:
            logger.info("Manual override to Telugu detected.")
            session.tts.update_options(voice="Anusha", locale="te-IN", style="Conversational")
            assistant.language = "Telugu"
        elif has_tamil or "ta" in detected_lang or words.intersection(tamil_keywords):
            logger.info(f"Tamil language detected (lang: {detected_lang}). Switching TTS to Karthikeyan (ta-IN).")
            session.tts.update_options(voice="Karthikeyan", locale="ta-IN", style="Conversational")
            assistant.language = "Tamil"
        elif has_telugu or "te" in detected_lang or words.intersection(telugu_keywords):
            logger.info(f"Telugu language detected (lang: {detected_lang}). Switching TTS to Anusha (te-IN).")
            session.tts.update_options(voice="Anusha", locale="te-IN", style="Conversational")
            assistant.language = "Telugu"
        elif has_devanagari or "hi" in detected_lang or words.intersection(hindi_keywords):
            logger.info(f"Hindi language detected (lang: {detected_lang}). Switching TTS to Anisha (hi-IN).")
            session.tts.update_options(voice="Anisha", locale="hi-IN", style="Conversation")
            assistant.language = "Hindi"
        else:
            if assistant.language == "English":
                logger.info(f"English language detected (lang: {detected_lang}). Switching TTS to Anisha (en-IN).")
                session.tts.update_options(voice="Anisha", locale="en-IN", style="Conversation")
                assistant.language = "English"



    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    assistant = Assistant(user_id=user_id, initial_info=initial_info, is_sip=is_sip)
    if hasattr(session.tts, "assistant_ref"):
        session.tts.assistant_ref = assistant
        
    # Configure assistant language and TTS voice options based on loaded caller profile language preference
    if caller_profile:
        lang_pref = caller_profile.get("language_preference")
        if lang_pref == "Tamil":
            logger.info("Initializing session with Tamil language preference from user profile.")
            session.tts.update_options(voice="Karthikeyan", locale="ta-IN", style="Conversational")
            assistant.language = "Tamil"
        elif lang_pref == "Telugu":
            logger.info("Initializing session with Telugu language preference from user profile.")
            session.tts.update_options(voice="Anusha", locale="te-IN", style="Conversational")
            assistant.language = "Telugu"
        elif lang_pref == "Hindi":
            logger.info("Initializing session with Hindi language preference from user profile.")
            session.tts.update_options(voice="Anisha", locale="hi-IN", style="Conversation")
            assistant.language = "Hindi"

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()
    
    # Establish unique call ID and initialize database logging
    room_sid = ctx.room.sid
    if asyncio.iscoroutine(room_sid) or hasattr(room_sid, "__await__"):
        room_sid = await room_sid
    call_id = room_sid if room_sid else f"call_{uuid.uuid4().hex[:12]}"
    call_type = "SIP" if is_sip else "BROWSER"
    assistant.call_id = call_id
    
    from db import start_call_outcome, update_call_outcome
    start_call_outcome(call_id=call_id, user_id=user_id, call_type=call_type, language=assistant.language)
    
    # Track execution cleanup state
    cleanup_done = False
    
    async def cleanup_call():
        nonlocal cleanup_done
        if cleanup_done:
            return
        cleanup_done = True
        logger.info(f"Cleaning up call session: {assistant.call_id}")
        outcome = "SUCCESS" if assistant.call_goal_completed else "FAILED"
        success_reason = assistant.success_reason
        if outcome == "FAILED" and not success_reason:
            success_reason = "Incomplete call"
            
        update_call_outcome(
            call_id=assistant.call_id,
            outcome=outcome,
            success_reason=success_reason,
            scheme_name=assistant.scheme_name,
            information_requested=assistant.information_requested,
            language=assistant.language
        )

    # Register cleanup handlers
    ctx.add_shutdown_callback(cleanup_call)
    
    @ctx.room.on("disconnected")
    def on_disconnected():
        logger.info("Room disconnected, updating call outcome.")
        asyncio.create_task(cleanup_call())


    @ctx.room.on("dtmf_received")
    def on_dtmf_received(participant: rtc.RemoteParticipant, code: int, digit: str):
        logger.info(f"DTMF received from participant {participant.identity}: code={code}, digit={digit}")
        if is_sip and digit == "1":
            logger.info("DTMF 1 received. Initiating opt-out shutdown...")
            async def shutdown():
                try:
                    session.interrupt()
                    session.clear_user_turn()
                    await session.say("Understood. I won't continue this call and will make sure you are not contacted again. Thank you, and have a good day.", allow_interruptions=False)
                    await asyncio.sleep(5.0)
                except Exception as e:
                    logger.error(f"Error during opt-out: {e}")
                finally:
                    await ctx.room.disconnect()
            asyncio.create_task(shutdown())
            
        elif is_sip and digit == "2":
            logger.info("DTMF 2 received. Continuing call...")
            async def continue_call():
                try:
                    session.interrupt()
                    session.clear_user_turn()
                    await session.say("Great! Let's continue. I can explain Indian government financial schemes such as PMJDY, APY, PMSBY, PMJJBY, and PM MUDRA Yojana. What would you like to learn about?", allow_interruptions=True)
                except Exception as e:
                    logger.error(f"Error during continue: {e}")
            asyncio.create_task(continue_call())

    if is_sip:
        greeting_text = "Hello, this is FinBuddy, an AI financial information assistant. I'm calling to inform you about newly launched and updated government financial schemes, including the Pradhan Mantri MUDRA Yojana. To stop this call and make sure you are not contacted again, please tell 1. To continue this call and hear about the schemes, please tell 2."
        if initial_info:
            try:
                caller_data = json.loads(initial_info)
                name = caller_data.get("name")
                if name:
                    greeting_text = f"Hello {name}, this is FinBuddy, an AI financial information assistant. I'm calling to inform you about newly launched and updated government financial schemes, including the Pradhan Mantri MUDRA Yojana. To stop this call and make sure you are not contacted again, please tell 1. To continue this call and hear about the schemes, please tell 2."
            except Exception:
                pass

        async def greet_sip():
            await asyncio.sleep(0.5)
            logger.info("SIP Participant connected. Speaking outbound greeting immediately...")
            await session.say(greeting_text, allow_interruptions=True)

        asyncio.create_task(greet_sip())


if __name__ == "__main__":
    cli.run_app(server)
