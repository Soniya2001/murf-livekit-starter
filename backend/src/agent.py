import logging
import json
import asyncio

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
    function_tool,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from db import get_caller, save_caller
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
- Do NOT answer specific details about government financial schemes (such as eligibility criteria, benefits, premiums, application processes, or required documents) from memory.
- You MUST call the `lookup_government_scheme` tool whenever the user asks for information about a specific government financial scheme (e.g. PMJDY, APY, PMJJBY, PMSBY, PMMY / PM Mudra, Stand-Up India, JanSamarth).
- When explaining the retrieved information, tell the user the official source and source update date. Say: "According to information sourced from the official government portal [source], last updated on [source_updated_at]..." Keep it clean and easy to say. Do NOT refer to retrieved_at as the time the official government website was accessed.
- Summarize long text naturally for a spoken conversation. Do not read raw lists or complex tables.
- Knowledge stops at: Personal account details, transaction processing, and making final approvals or commitments on behalf of any institution.

# LANGUAGE
- Mirror the user's mix of languages (e.g., English, Tamil, Telugu, Hindi, or a mix) naturally.
- Maintain a polite, respectful, and helpful tone.
- Keep the language simple and accessible, avoiding complex banking jargon.

# GUARDRAILS
- **CRITICAL**: Never ask for or accept an OTP (One-Time Password), PIN, password, or bank account number.
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
            caller = get_caller(user_id)
            if caller:
                initial_info = json.dumps(caller)
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
        tts=murf.TTS(
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
            "kya", "hai", "aur", "main", "haan", "nahin", "aap", "namaste", "shukriya",
            "yojana", "batao", "bataiye", "samjhao", "dhan", "suraksha", "bima", "pension",
            "mein", "ke", "ki", "se", "ko", "ka", "jo", "toh", "bhi", "ho", "kar", "raha",
            "rahi", "rha", "rhi", "mujhe", "mera", "meri", "hum", "tum", "apna", "apni",
            "karke", "karo", "karna", "tha", "thi", "the", "ab", "kab", "tab", "sab"
        }

        # Check for common Tanglish/Tamil romanized keywords
        tamil_keywords = {
            "vanakkam", "nandri", "aama", "illa", "enaku", "ungalukku", "theriyum", "theriyathu",
            "panna", "pannunga", "solla", "sollunga", "keta", "kelunga", "panam", "kaasu",
            "bank", "vangi", "semipu", "kadan", "bima", "pension", "thittam", "yojana", "scheme",
            "naan", "neenga", "avanga", "ivan", "iru", "iruku", "irukanga", "yen", "eppadi",
            "eppo", "enga", "enna", "romba", "nalla", "veedu", "kaala", "nalla-irukingala"
        }

        # Check for common Telugu/Telish romanized keywords
        telugu_keywords = {
            "namaskaram", "dhanyavadalu", "avunu", "kadu", "naku", "meeku", "telusu", "teliyadu",
            "cheyandi", "cheyyali", "cheppandi", "panam", "dhanam", "bank", "vaddi", "pension",
            "bima", "yojana", "pathakam", "scheme", "nenu", "meeru", "varu", "vadu", "ela",
            "eppudu", "ekkada", "enti", "chala", "bagundi", "illu", "kalam", "namaste"
        }

        words = set(transcript.split())

        # Check detected language from STT event
        detected_lang = (getattr(ev, "language", "") or "").lower()

        if has_tamil or "ta" in detected_lang or words.intersection(tamil_keywords):
            logger.info(f"Tamil language detected (lang: {detected_lang}). Switching TTS to Karthikeyan (ta-IN).")
            session.tts.update_options(voice="Karthikeyan", locale="ta-IN", style="Conversational")
        elif has_telugu or "te" in detected_lang or words.intersection(telugu_keywords):
            logger.info(f"Telugu language detected (lang: {detected_lang}). Switching TTS to Anusha (te-IN).")
            session.tts.update_options(voice="Anusha", locale="te-IN", style="Conversational")
        elif has_devanagari or "hi" in detected_lang or words.intersection(hindi_keywords):
            logger.info(f"Hindi language detected (lang: {detected_lang}). Switching TTS to Anisha (hi-IN).")
            session.tts.update_options(voice="Anisha", locale="hi-IN", style="Conversation")
        else:
            logger.info(f"English language detected (lang: {detected_lang}). Switching TTS to Anisha (en-IN).")
            session.tts.update_options(voice="Anisha", locale="en-IN", style="Conversation")

    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(user_id=user_id, initial_info=initial_info, is_sip=is_sip),
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
