# Backend — Voice Agent with Murf Falcon TTS

The Python backend for the Voice Agent Starter. It runs a real-time voice AI pipeline using [LiveKit Agents](https://docs.livekit.io/agents), connecting Murf Falcon TTS, Deepgram STT, and Google Gemini into a single conversational agent.

## How It Works

```
User speaks → [Deepgram STT] → text → [Gemini LLM] → response → [Murf Falcon TTS] → audio → User hears
```

LiveKit handles the real-time audio transport. The agent connects to LiveKit as a participant, listens for user speech, and responds with synthesized audio.

## Setup

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env.local
```

Fill in your keys in `.env.local`:

| Variable             | Where to get it                                           |
| -------------------- | --------------------------------------------------------- |
| `LIVEKIT_URL`        | [LiveKit Cloud](https://cloud.livekit.io/) → Settings     |
| `LIVEKIT_API_KEY`    | [LiveKit Cloud](https://cloud.livekit.io/) → Settings     |
| `LIVEKIT_API_SECRET` | [LiveKit Cloud](https://cloud.livekit.io/) → Settings     |
| `MURF_API_KEY`       | [murf.ai/api/dashboard](https://murf.ai/api/dashboard)    |
| `DEEPGRAM_API_KEY`   | [deepgram.com](https://console.deepgram.com/)             |
| `GOOGLE_API_KEY`     | [aistudio.google.com](https://aistudio.google.com/apikey) |

For LiveKit Cloud users, you can auto-populate LiveKit credentials:

```bash
lk cloud auth
lk app env -w -d .env.local
```

### 3. Download models

```bash
uv run python src/agent.py download-files
```

This downloads Silero VAD and the LiveKit turn detector models.

### 4. Run the agent

```bash
# Development mode (auto-reload)
uv run python src/agent.py dev

# Or test directly in your terminal (no frontend needed)
uv run python src/agent.py console

# Production
uv run python src/agent.py start
```

## Configuration

All configuration lives in [`src/agent.py`](src/agent.py).

### System prompt

The `SYSTEM_PROMPT` constant at the top of `agent.py` controls what your agent does. Change it to build any voice-powered use case.

#### Example prompts

**Customer Support (default):**

```
You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate.
```

**Language Tutor:**

```
You are a patient and encouraging language tutor helping the user practice conversational Spanish. Speak primarily in Spanish but switch to English to explain grammar or vocabulary when needed. Correct mistakes gently and suggest better phrasing. Keep conversations natural and fun.
```

**AI Receptionist:**

```
You are a professional receptionist for a medical clinic. Help callers schedule appointments, answer questions about office hours and services, and take messages for doctors. Be warm but efficient. Ask for the caller's name and reason for calling upfront.
```

**Interview Coach:**

```
You are an experienced interview coach. Conduct mock interviews with the user for software engineering roles. Ask one behavioral or technical question at a time, let the user answer fully, then give specific feedback on their response — what was strong, what could improve, and a suggested reframe. Keep the tone encouraging but honest.
```

**Sales Assistant:**

```
You are a knowledgeable sales assistant for an electronics store. Help customers find the right product by asking about their needs, budget, and preferences. Compare options clearly, highlight trade-offs, and make a recommendation. Never be pushy — focus on helping the customer make the best decision for them.
```

**Fitness Coach:**

```
You are an upbeat personal fitness coach. Help users plan workouts, suggest exercises for specific muscle groups, and answer questions about form and technique. Ask about their fitness level and any injuries before recommending exercises. Keep instructions clear and motivating.
```

**Storyteller / Bedtime Narrator:**

```
You are a creative storyteller who tells original bedtime stories for children aged 4–8. Ask the child (or parent) for a character name, a favorite animal, and a setting, then weave a short, calming story. Use vivid but simple language. End each story on a peaceful, sleepy note.
```

**Meeting Summarizer:**

```
You are a meeting assistant. The user will describe what happened in a meeting or read you their notes. Summarize the key decisions, action items (with owners if mentioned), and any open questions. Be concise and structured. Ask clarifying questions if something is ambiguous.
```

**Trivia Game Host:**

```
You are an enthusiastic trivia game host. Ask the user one trivia question at a time from a mix of categories — science, history, pop culture, geography, and sports. Wait for their answer, tell them if they're right or wrong, give a brief fun fact, then move to the next question. Keep score and announce it every 5 questions.
```

**Mental Health Check-in Companion:**

```
You are a gentle, non-clinical wellness companion. Help users talk through their day, reflect on how they're feeling, and practice simple grounding exercises like deep breathing or gratitude lists. You are not a therapist — if the user expresses serious distress or mentions self-harm, gently encourage them to reach out to a professional or crisis helpline.
```

### Voice

Set the `voice` argument in the `murf.TTS(...)` call:

```python
tts=murf.TTS(
    voice="en-US-matthew",    # Change this
    style="Conversation",
    tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
    text_pacing=True
)
```

Some voice options:

| Voice ID | Description                      |
| -------- | -------------------------------- |
| `Anisha` | Indian English, female (default) |
| `Pooja`  | Indian English, female           |
| `Samar`  | Indian English, male             |
| `Amara`  | US English, female               |
| `Hazel`  | UK English, female               |
| `Bertie` | UK English, male                 |
| `Gordon` | US English, male                 |

Browse all 150+ voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### STT (Speech-to-Text)

Default is Deepgram Nova-3. Change in the `AgentSession(stt=...)` call:

```python
stt=deepgram.STT(model="nova-3")
```

### LLM

Default is Google Gemini. To switch:

- **Gemini (default):** Set `GOOGLE_API_KEY` in `.env.local`
- **OpenAI:** Set `OPENAI_API_KEY`, install `livekit-agents[openai]`, and change the `llm=` argument

## Testing

The project includes an eval suite based on the LiveKit Agents [testing framework](https://docs.livekit.io/agents/build/testing/):

```bash
uv run pytest
```

Tests are in [`tests/test_agent.py`](tests/test_agent.py) and use LLM-as-judge evaluations to verify the agent behaves correctly (friendly greetings, grounding, refusing harmful requests).

To run tests in CI, you'll need to add `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` as repository secrets.

## Deployment

### Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/tIVCF1?referralCode=cNjn2P&utm_medium=integration&utm_source=template&utm_campaign=generic)

Set these environment variables in Railway:

- `MURF_API_KEY`
- `DEEPGRAM_API_KEY`
- `GOOGLE_API_KEY`
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`

### Docker

A production-ready [Dockerfile](Dockerfile) is included:

```bash
docker build -t murf-voice-agent .
docker run --env-file .env.local murf-voice-agent
```

## Project Structure

```
backend/
├── src/
│   └── agent.py          # Agent entrypoint — pipeline, prompt, config
├── tests/
│   └── test_agent.py     # LLM-judged eval suite
├── .env.example           # Environment variable template
├── pyproject.toml         # Python dependencies (uv)
├── Dockerfile             # Production container
└── railway.toml           # Railway deploy config
```

## Links

- [Murf Falcon TTS Docs](https://murf.ai/api/docs/text-to-speech/streaming)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Agents Docs](https://docs.livekit.io/agents)
- [Deepgram Nova-3 Docs](https://developers.deepgram.com)

## Day 5 – Grounding FinBuddy in Real Data

To prevent hallucinations, FinBuddy is grounded in official government data.

1. **Mandatory Disclosure**: FinBuddy currently uses a locally curated government-scheme dataset sourced from official government portals. It is not a live government API and may not reflect changes made after the recorded source update date. Users should verify important information through the relevant official government or financial institution.
2. **Data Source Verification Details**:
   - **PMJDY**: [Official Portal](https://www.pmjdy.gov.in/) (Source Last Updated: May 20, 2026)
   - **APY**: [Official Portal](https://www.npscra.nsdl.co.in/scheme-atal-pension-yojana.php) (Source Last Updated: June 15, 2026)
   - **PMJJBY**: [Official Portal](https://www.jansuraksha.gov.in/) (Source Last Updated: April 10, 2026)
   - **PMSBY**: [Official Portal](https://www.jansuraksha.gov.in/) (Source Last Updated: April 10, 2026)
   - **PMMY (PM MUDRA)**: [Official Portal](https://www.mudra.org.in/) (Source Last Updated: February 5, 2026)
   - **Stand-Up India**: [Official Portal](https://www.standupmitra.in/) (Source Last Updated: March 12, 2026)
   - **JanSamarth**: [Official Portal](https://www.jansamarth.in/) (Source Last Updated: April 18, 2026)
3. **Tool Name**: `lookup_government_scheme(scheme_name: str, information_requested: str)`
4. **Tool Description**: Tells the LLM to query the database whenever specific scheme details are needed rather than answering from memory.
5. **Data Freshness**: Every successful tool invocation returns the source URL, update timestamps, and retrieval timestamp, which the agent mentions to the user. It explicitly separates the source update date from local access times.
6. **Error & Failure Path Handling**:
   - Simulated Timeout: Inputting a query containing the word `"timeout"` triggers a simulated API timeout.
   - Connection/HTTP Failures: Handles connection issues gracefully, returning structured exceptions. The agent reports: *"I'm unable to reach the government information source right now. I don't want to guess or provide outdated information. Please try again shortly."*
   - Schemes Not Found: Returns a `NOT_FOUND` error, making the agent report: *"I don't currently have verified information about that scheme in my government-scheme dataset, so I don't want to guess. You can check the relevant official government portal for the latest information."*
   - Unrecognized Fields: Returns a `FIELD_NOT_AVAILABLE` error, making the agent report: *"I don't currently have verified information for that specific aspect of the scheme in my current dataset, so I don't want to guess. Please check the relevant official government portal."*
7. **Example Voice Queries**:
   - "What is APY?"
   - "What are the eligibility requirements for PMJDY?"
   - "What is a Mudra loan?"
   - "Explain a fictional scheme XYZ"

## Day 8 – Call Outcome Tracking

### Success Definition
"A successful Financial Services call is one in which the caller completes a government-scheme eligibility check or receives a requested government-scheme document list."

### Allowed Outcomes
- **SUCCESS**: Achieved when either:
  1. **Eligibility Enquiry Completed**: The requested scheme was identified, required information gathered, and the agent explained eligibility criteria (stating that final eligibility is determined by the relevant authority).
  2. **Document List Provided**: The agent successfully retrieves and provides the available scheme document list.
- **FAILED**: Achieved when the conversation ends without meeting a success condition (e.g., caller hangs up early, leaves before documents are listed, or a technical connection/voice pipeline error occurs).

### Call Lifecycle & Storage
- Call records are initially created at call/session start as `IN_PROGRESS`.
- At call end, the final outcome is evaluated and saved into SQLite (`call_outcomes` table).
- The actual LiveKit room session ID (`ctx.room.sid`) serves as the unique `call_id` to ensure consistent mapping from start to finish.

### Database Schema
The database uses the `call_outcomes` table with fields:
- `id`: Auto-incrementing primary key
- `call_id`: Unique identifier (LiveKit session ID)
- `user_id`: Anonymous participant identifier
- `call_type`: Connection channel (`BROWSER` or `SIP`)
- `started_at`/`ended_at`: Call start/end timestamps
- `duration_seconds`: Calculated call duration
- `outcome`: `SUCCESS` or `FAILED`
- `success_reason`: Breakdown detail (e.g. `"Eligibility check completed"`, `"Document list provided"`)
- `scheme_name` / `information_requested`: Curated metadata about the interaction
- `language`: Call language (Hindi, Tamil, Telugu, English)

### Dashboard UI & API
- **Web Dashboard**: Access `/call-analytics` or `/dashboard` to view dynamic statistics pulled directly from the SQLite database.
- **Metrics**: Displays `TOTAL CALLS`, `SUCCESSFUL CALLS`, `FAILED CALLS`, and `Success Rate %` dynamically (zero-rate handled safely).
- **Privacy Protections**: Never displays, parses, or stores sensitive variables (like OTPs, PINs, passwords, bank account numbers, credentials, or full transcripts).

### Testing Instructions
To run automated analytics tests:
```bash
uv run pytest tests/test_analytics.py
```

## License

MIT — see [LICENSE](LICENSE).

