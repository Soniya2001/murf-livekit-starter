import logging

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
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

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

# KNOWLEDGE
- Deep knowledge of major government financial schemes (e.g., pension schemes like APY, insurance schemes like PMJJBY/PMSBY, and subsidy programs).
- Understanding of general banking concepts, digital banking security, and safe online practices.
- Knowledge stops at: Personal account details, transaction processing, and making final approvals or commitments on behalf of any institution.

# LANGUAGE
- Mirror the user's mix of languages (e.g., English, Tamil, Telugu, Hindi, or a mix) naturally.
- Maintain a polite, respectful, and helpful tone.
- Keep the language simple and accessible, avoiding complex banking jargon.

# GUARDRAILS
- **CRITICAL**: Never ask for or accept an OTP (One-Time Password), PIN, password, or bank account number.
- **CRITICAL**: Never promise or guarantee scheme approval, loan disbursement, or financial payouts.
- **Escalation Script / Refusal**: If a user asks about account-specific actions, transaction processing, or demands approvals, say: "For your security, I cannot ask for or process OTPs, PINs, or account details, and I cannot guarantee scheme approvals. Please contact your official bank branch directly for assistance with your account."

# STYLE
- Keep responses short and conversational, suitable for a spoken voice assistant.
- Use simple punctuation; avoid bullet lists with complex symbols or emojis that are hard to speak.
- Maintain a comfortable conversational pace.
- If the user is silent, gently check in: "Are you still there? Let me know how I can help."
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


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
                voice="Karthikeyan", 
                locale="ta-IN",
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

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
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
        agent=Assistant(),
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


if __name__ == "__main__":
    cli.run_app(server)
