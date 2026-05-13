# Customer support voice agent with order lookup

A runnable customer support voice agent that takes calls, transcribes the caller, looks up orders, initiates returns, schedules callbacks, and transfers to a human — all through the AssemblyAI Voice Agent API in a single WebSocket.

**Stack**

- **Voice Agent API:** AssemblyAI (one WebSocket = STT + LLM + TTS + turn detection + tool calling)
- **Audio:** PyAudio for microphone capture and playback (browser/Twilio variants in `transports/`)
- **Tools:** `get_order_status`, `initiate_return`, `schedule_callback`, `transfer_to_human`

**Why the Voice Agent API for customer support**

One bill ($4.50/hr flat), one set of logs, and Universal-3 Pro Streaming under the hood — which means 307ms P50 latency and 21% fewer alphanumeric errors than the previous generation of streaming STT. Order IDs are alphanumeric. That accuracy is the difference between "the agent worked first try" and "the caller had to repeat themselves three times."

---

## What's in scope

The agent in this repo is intentionally narrow. It handles:

- Order status lookups by order ID
- Return initiation for delivered orders
- Callback scheduling
- Clean transfer to a human agent

It does **not** handle:

- Open-ended product questions (would need a knowledge base + retrieval)
- Account changes that need identity verification beyond order ID
- Off-policy refunds or disputes (always transfer)

This scoping is deliberate. Tier-1 deflection agents ship when they do one thing well.

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# edit .env and add your AssemblyAI key
```

Get a key at [assemblyai.com/dashboard/signup](https://www.assemblyai.com/dashboard/signup).

### 3. Run the agent

```bash
python agent.py
```

You'll hear the agent greet you. Try saying:

- "My order ID is A B 3 7 9 2"
- "I want to return order E F 5 5 6 6"
- "Can someone call me back at six one seven five five five one two one two"
- "I want to speak to a person"

---

## What's in each file

| File | Purpose |
|---|---|
| `agent.py` | Main agent loop. Opens the Voice Agent API WebSocket, streams mic audio in, plays responses, routes tool calls. |
| `tools.py` | Tool definitions and dispatcher with stub backends. Replace stubs with your real OMS / returns / scheduling APIs. |
| `prompts.py` | System prompt with scope rules and confirmation behavior. |
| `audio.py` | PyAudio microphone capture and speaker playback. |
| `requirements.txt` | Python deps. |
| `.env.example` | Required environment variables. |

---

## Connecting to your real systems

Replace the stubs in `tools.py`:

| Tool | Stub | Replace with |
|---|---|---|
| `get_order_status` | Hard-coded dict | Your OMS / Shopify / ERP order lookup |
| `initiate_return` | Print statement | Your returns API + label email |
| `schedule_callback` | Print statement | Your scheduling backend (Salesforce, Front, custom) |
| `transfer_to_human` | Print statement | Your contact center handoff (Zendesk Talk, Five9, custom) |

For `transfer_to_human` specifically: pass the full conversation history to the human agent so the caller doesn't repeat themselves. The Voice Agent API gives you `transcript.user.final` and `transcript.agent.final` events you can write to your CRM during the call.

---

## Going to production

- **Wrap the agent in your telephony layer.** This repo runs the agent locally with microphone audio for testing. For phone calls, bridge through Twilio Media Streams — see the companion `twilio-voice-agent-assemblyai` repo.
- **Add session persistence.** Track each call by `session_id` in a Redis or Postgres store so you can resume, audit, and analyze.
- **Add PII redaction on logs.** Order IDs are fine to log; phone numbers and email addresses should be redacted before they hit your warehouse.
- **Set up real-time analytics.** Score every call for completion (did the agent finish the task?), escalation rate, and average handle time. Feed regressions back into the prompt.
- **Test the hard cases.** Record 50 real calls (with consent) and replay them. Background noise, accents, hesitations, and people reading IDs character-by-character vs. all at once will all stress the agent differently.

---

## Cost

Voice Agent API: **$4.50 per hour** of session time. For a 3-minute average call, that's ~$0.23/call all-in (STT + LLM + TTS + turn detection + tool calling).

Tool implementations are billed by whatever backend they call — typically free or pennies per call.

---

## License

MIT.
