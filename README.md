# Voice Agent Starter — Powered by Murf Falcon

Build a production voice AI agent in 5 minutes. Powered by the fastest TTS on the market - swap the system prompt to build anything from customer support to language tutors.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## Why Murf Falcon

- **55ms model latency** - fastest production TTS
- **130ms time-to-first-audio** across 10+ global regions
- **$0.01/1000 characters** - up to 10x cheaper than alternatives
- **150+ voices** across 35+ languages
- **99.38% pronunciation accuracy**

---

## Architecture

```mermaid
flowchart LR
    A[🎙️ User speaks] -->|audio| B[Deepgram STT]
    B -->|text| C[LLM]
    C -->|response text| D[Murf Falcon TTS]
    D -->|audio| E[LiveKit]
    E -->|stream| F[🔊 User hears]

    style A fill:#444441,stroke:#888780,color:#fff
    style B fill:#185FA5,stroke:#85B7EB,color:#fff
    style C fill:#534AB7,stroke:#AFA9EC,color:#fff
    style D fill:#0F6E56,stroke:#5DCAA5,color:#fff
    style E fill:#D85A30,stroke:#F0997B,color:#fff
    style F fill:#444441,stroke:#888780,color:#fff
```

---

## Quickstart

### Prerequisites

- **Python** 3.10+
- **[uv](https://docs.astral.sh/uv/)** - fast Python package manager
  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Node.js** 18+
- **pnpm** — fast Node package manager
  ```bash
  npm install -g pnpm
  ```
- A [LiveKit](https://cloud.livekit.io/) project (free tier available)

### Step 1: Clone the repo

```bash
git clone https://github.com/murf-ai/murf-livekit-starter.git
cd murf-livekit-starter
```

### Step 2: Set up environment variables

Create `.env.local` in both `backend/` and `frontend/` (copy from `.env.example` in each). You need:

| Variable                               | Where to get it                                        | Required |
| -------------------------------------- | ------------------------------------------------------ | -------- |
| `LIVEKIT_URL`                          | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_KEY`                      | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_SECRET`                   | LiveKit Cloud dashboard                                | Yes      |
| `MURF_API_KEY`                         | [murf.ai/api/dashboard](https://murf.ai/api/dashboard) | Yes      |
| `DEEPGRAM_API_KEY`                     | [deepgram.com](https://deepgram.com)                   | Yes      |
| `GOOGLE_API_KEY` (or `OPENAI_API_KEY`) | Depends on LLM choice                                  | Yes      |

### Step 3: Install backend dependencies

```bash
cd backend
uv sync
uv run python src/agent.py download-files
```

### Step 4: Install frontend dependencies

```bash
cd frontend
pnpm install
```

### Step 5: Run it

**Option A - All-in-one (from repo root):**

```bash
# macOS/Linux
chmod +x start_app.sh
./start_app.sh

# Windows (PowerShell)
.\start_app.ps1
```

**Option B - Separate terminals:**

```bash
# Terminal 1 — LiveKit Server
livekit-server --dev

# Terminal 2 — Backend agent
cd backend && uv run python src/agent.py dev

# Terminal 3 — Frontend
cd frontend && pnpm dev
```

Then open **http://localhost:3000** in your browser.

You should now see the voice agent UI. Click **Start talking**, allow microphone access, and speak — the agent will respond with Murf Falcon TTS. Ensure your backend and (if using Option B) LiveKit server are running.

---

## Deploy

Want to deploy this beyond localhost? You'll need to deploy **two services**: the backend agent and the frontend. Both must use the same LiveKit project.

> This is a two-service app — the backend agent and the frontend UI deploy separately. You'll need both running and connected to the same LiveKit project.

### Backend (Python agent) — Deploy to Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/tIVCF1?referralCode=cNjn2P&utm_medium=integration&utm_source=template&utm_campaign=generic)

Set these environment variables in Railway:

- `MURF_API_KEY`
- `DEEPGRAM_API_KEY`
- `GOOGLE_API_KEY` or `OPENAI_API_KEY`
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

The backend runs as a long-lived Python process that connects to LiveKit as an agent. Railway handles this well.

### Frontend (Next.js) — Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/murf-ai/murf-livekit-starter&root-directory=frontend&env=LIVEKIT_URL,LIVEKIT_API_KEY,LIVEKIT_API_SECRET&project-name=murf-voice-agent&repository-name=murf-voice-agent)

Set these environment variables in Vercel:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `AGENT_NAME` (optional — for explicit agent dispatch)

The frontend is a standard Next.js app. Point it at the same LiveKit instance your backend agent is connected to.

### Connecting them

The frontend and backend don't call each other directly — they both connect to **LiveKit**, which handles the real-time audio transport.

1. Use the **same** `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` on both Railway and Vercel
2. Set `AGENT_NAME=my-agent` on Vercel — this matches the `agent_name="my-agent"` registered in `backend/src/agent.py`
3. Verify: Railway logs should show the agent connected to LiveKit. Open your Vercel URL, click **Start talking** — the agent should respond

If the agent doesn't connect, double-check that both services point to the same LiveKit project and that the backend is running (check Railway logs).

---

## Change the Use Case

The default system prompt makes this a **customer support agent**. You can change the agent’s behavior by editing the prompt.

**Where the prompt lives:** `backend/src/agent.py`- the `SYSTEM_PROMPT` constant (near the top of the file, after the imports). Change that string to change what your voice agent does.

### Example prompts (copy-paste)

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

See the Configuration section below for voice, STT, and LLM options.

---

## Configuration

### Murf voice

Edit the `tts=murf.TTS(...)` call in `backend/src/agent.py`. Set the `voice` argument to any Murf voice ID. Examples:

- `Anisha` — Indian English (female, default in this starter)
- `Pooja` — Indian English (female)
- `Samar` — Indian English (male)
- `Amara` — US English (female)
- `Gordon` — US English (male)
- `Hazel` — UK English (female)
- `Bertie` — UK English (male)

Browse all voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### STT provider

STT is configured in `backend/src/agent.py` in the `AgentSession(stt=...)` call. The default is Deepgram (`deepgram.STT(model="nova-3")`). You can swap to another LiveKit-compatible STT plugin if needed.

### LLM (Gemini vs OpenAI)

- **Gemini (default):** Set `GOOGLE_API_KEY` and use `llm=google.LLM(model="gemini-3.5-flash-lite")` in `agent.py`.
- **OpenAI:** Set `OPENAI_API_KEY`, add the OpenAI plugin, and use the corresponding `llm=openai.LLM(...)` in `agent.py`.

### Audio format

Murf Falcon and LiveKit handle audio format internally. For advanced options, see [Murf API docs](https://murf.ai/api/docs) and [LiveKit docs](https://docs.livekit.io).

---

## Project Structure

```
murf-livekit-starter/
├── backend/                 # Python voice agent (LiveKit Agents + Murf Falcon)
│   ├── src/
│   │   └── agent.py         # Agent entrypoint, pipeline (STT/LLM/TTS), system prompt
│   ├── tests/               # Agent tests
│   ├── .env.example         # Backend env template
│   ├── pyproject.toml       # Python deps (uv)
│   └── railway.toml         # Railway deploy config
├── frontend/                # Next.js UI for voice sessions
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   └── api/token/       # LiveKit token endpoint (dev)
│   ├── components/          # UI (agents-ui, app config, theme)
│   ├── app-config.ts        # Branding, title, button text, accent
│   ├── .env.example         # Frontend env template
│   └── package.json         # Node deps (pnpm)
├── start_app.sh             # Start LiveKit + backend + frontend (macOS/Linux)
├── start_app.ps1            # Start LiveKit + backend + frontend (Windows)
├── README.md                # This file
```

For deeper documentation on each part, see:

- [Backend Documentation](./backend/README.md) — agent pipeline, voice/LLM/STT configuration, testing, deployment
- [Frontend Documentation](./frontend/README.md) — UI customization, visualizers, theming, component architecture

---

# 10 Days of Voice Agents – VoiceForBharat Edition

This section tracks the daily progress of **FinBuddy**, our AI Financial Voice Assistant, implemented during the "10 Days of Voice Agents" series:

### Day 2 – Multilingual Support & Voice Switching
- Added Hindi, Tamil, Telugu, and Indian English language options to the LLM instructions.
- Implemented real-time dynamic language detection using custom text classifiers and romanized Hinglish/native keyboard character scanners.
- Integrated Murf Falcon TTS with dynamic model configuration updating (updating locale, gender, style, and voice characteristics on-the-fly depending on the spoken language).

### Day 3 – Beautiful Multilingual Web Client
- Customized the web client UI for a premium experience, including a custom FinBuddy avatar, logo, brand assets, and custom gradients.
- Added translation dictionary infrastructure to localize buttons, indicators, headings, and interface strings across all supported languages (Tamil, Telugu, Hindi, English).
- Created a dynamic card layout welcome dashboard showing government financial scheme quick-links.

### Day 4 – SQLite Caller Memory & Consent
- Designed a SQLite caller database (`finbuddy_memory.db`) to persist visitor history.
- Integrated a consent-based memory system (`db.py` and tools). If the user consents, the agent uses the `save_caller_details` tool to store their name, spoken language, and checked eligibility criteria.
- Personalized subsequent greetings dynamically for return callers.

### Day 5 – Government Scheme Lookup Tool
- Created the government schemes dataset (`schemes_data.py`) listing accurate information, benefits, and eligibility rules for key programs (PM MUDRA Yojana, APY, PMJDY, PMSBY, PMJJBY).
- Integrated a local lookup tool allowing the LLM to dynamically retrieve official information to prevent hallucinations.
- Added 18 unit tests (`tests/test_schemes.py`) to verify the accuracy of scheme matching, query handling, and safety guardrails.

### Day 6 – Outbound Voice Calls
- Added outbound telephony calling using LiveKit SIP integration.
- Supported immediate greetings on connection, DTMF keypad support (Key 1 to opt out/Key 2 to continue), and auto-hangup.

### Day 7 – Human-Help Escalation System
- Added a robust human-help escalation system allowing FinBuddy to hand off calls to human representatives when required.
- Implemented an `escalation_requests` SQLite table preserving caller facts while preventing sensitive credentials (OTP, PIN, passwords, account numbers) from ever being stored.
- Built a `create_escalation` LiveKit function tool with parameter validation, security scrubbing, and unique reference ID generation (`FIN-YYYYMMDD-XXXX`).
- Mandated a verbal multilingual consent flow where the caller must agree to the shared parameters before escalation.
- Created an administrative support dashboard `/escalations` to group, search, and update escalation statuses (`OPEN`, `IN_REVIEW`, `RESOLVED`, `CLOSED`).
- Extended coverage to outbound SIP calls and added comprehensive unit tests verifying data safety and escalation triggers.

### Day 8 – Call Outcome State Tracking & Analytics Dashboard
- Designed and implemented call outcome state tracking in `agent.py` to record detailed outcome metrics (`outcome`, `success_reason`, `scheme_name`, `information_requested`, `duration_seconds`, `language`).
- Configured explicit success conditions mapping to Financial Services objectives: completing an eligibility lookup (`"Eligibility check completed"`) or receiving a requested documents checklist (`"Document list provided"`), while other lookups like overview or benefits remain pending unless a success condition is completed.
- Handled voice interruptions and cleanup events cleanly using `SpeechCreatedEvent.speech_handle` done callbacks and connection state validation to ensure that calls cut abruptly before response playout are correctly marked as `FAILED`, while completed conversations remain recorded as `SUCCESS`.
- Created a Next.js call analytics dashboard `/call-analytics` to display call statistics (total calls, success rate, failed vs successful call distributions, language distributions, and recent call histories).
- Added comprehensive integration tests in `tests/test_integration_flow.py` covering timeout handling, NOT_FOUND results, successful lookups, voice interruptions, and clean hang-ups.

---

# Day 9 – Multi-Specialist Handoff Routing

We introduced a specialized multi-agent handoff router that delegates user conversations from the main assistant to two separate specialist agents depending on the intent.

## Architecture

```
                    FinBuddy Main Agent
                             |
                   Intent / Request Type
                        /          \
                       /            \
             Government Scheme    Cyber Fraud
                    |                  |
                    ▼                  ▼
            Scheme Specialist    Fraud Specialist
```

### Components and Responsibilities

1. **Main FinBuddy Agent (`Assistant`)**:
   - Handles general financial literacy, digital payment safety (e.g. UPI scams, compound interest, savings/budgeting definitions).
   - Decides whether a specialist is required and triggers the appropriate handoff.
   - For government schemes, announces: `"I'll connect you with my government scheme specialist, who can help with the details."`
   - For cyber fraud/scam questions, announces: `"I'll connect you with my cyber fraud and financial safety specialist, who can help you with the next steps."`

2. **Government Scheme Specialist (`GovernmentSchemeSpecialist`)**:
   - Responsibility: Provide accurate, simple, and source-grounded information about Indian government financial schemes.
   - Voice: Samar (male voice).

   - Handles: Scheme eligibility, benefits, application processes, required documents, scheme status, comparisons.
   - Defer lookup queries to: `lookup_government_scheme` tool.
   - Out-of-role topics: Calls the `return_to_main_agent` tool to return control back to the main assistant agent along with the context.
   - Final eligibility warning: Never guarantees approval; final eligibility is determined by the relevant authority.

3. **Cyber Fraud and Financial Safety Specialist (`CyberFraudSpecialist`)**:
   - Responsibility: Provide reassurance, immediate safety guidance, and clear next steps when users report scams (UPI scams, phishing links, fake banking/customer-care calls, compromised accounts, impersonation).
   - Voice: Samar (male voice).
   - Limits: NEVER ask for sensitive identifiers (OTP, PIN, passwords, account numbers, Aadhaar, PAN). If user shares, scrub immediately and state safety guardrail warning.
   - Next steps: Reassure, identify fraud type, advise contacting banks officially, handle escalation requests using `create_escalation` with explicit user consent.
   - Out-of-role topics: Calls the `return_to_main_agent` tool to return control back to the main assistant agent along with the context.

4. **Specialist Re-routing and Return (`return_to_main_agent`)**:
   - Implements a controlled handback loop-free routing mechanism. When a user asks an out-of-scope question or switches topics inside a specialist session (e.g., from scheme information to reporting cyber fraud), the specialist triggers the `return_to_main_agent` tool.
   - This passes the user's query, language, and intent context back to the main `Assistant`.
   - The main agent uses dynamic instructions context injection to automatically route the user to the correct target specialist (Government Specialist -> Main Agent -> Cyber Fraud Specialist) on its immediate turn.

5. **Multilingual and Native Script Support**:
   - Preserves user's detected language (English, Hindi, Tamil, Telugu) across the handoff.
   - Specialist agents greet the user and respond strictly using correct native scripts (Devanagari, Tamil, Telugu, Latin).

6. **Call Outcome success integration**:
   - Goal completions (e.g. document checklists or eligibility inquiries) are written back to the active session metrics, marking calls correctly as `SUCCESS` or `FAILED`.


## Running Handoff Tests

To execute handoff verification tests:
```bash
cd backend
.venv\Scripts\pytest tests/test_handoff.py
```



---

## Escalation Database Schema
The database contains the `escalation_requests` table with fields:
- `id` (INTEGER, Primary Key Auto-Increment)
- `reference_id` (TEXT, Unique)
- `user_id` (TEXT)
- `caller_name` (TEXT)
- `issue_summary` (TEXT)
- `what_happened` (TEXT)
- `agent_checks` (TEXT)
- `urgency` (TEXT)
- `language` (TEXT)
- `preferred_follow_up` (TEXT)
- `status` (TEXT, Default 'OPEN')
- `created_at` (TIMESTAMP, Default Current)

---

## Run Escalation Tests
To execute the backend test suites including the new escalation tests:
```bash
cd backend
.venv\Scripts\pytest
```

---

## Links

- [Murf API Docs](https://murf.ai/api/docs)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Docs](https://docs.livekit.io)
- [Deepgram Docs](https://developers.deepgram.com)
- [Murf Falcon Benchmarks](https://murf.ai/falcon/benchmarks)
- [TTS Latency Benchmarker](https://github.com/sahilsgupta/tts-latency-benchmarker) — run your own p50/p95 tests across providers
- [Murf Discord](https://discord.gg/FbKAy96Sz7)
- [Murf Startup Incubator](https://murf.ai/api) — 50M free characters for startups

---

## License

MIT
