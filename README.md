# MagicPin AI Challenge - Vera Bot

## Team: Vera

**Model:** Llama3-8B via Groq (cloud LLM, <2s response)

## Quick Start

### 1. Configure Environment

```bash
# Edit .env with your Groq API key (free at https://console.groq.com/keys)
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama3-8b-8192
```

### 2. Start Bot

```bash
cd F:\Projects\magicpin-ai-challenge
py -m uvicorn src.bot:app --host 0.0.0.0 --port 8080
```

### 3. Get Public URL (ngrok)

```bash
py start_ngrok.py
```

### 4. Test

```bash
py test_smoke.py
```

### 5. Run Judge

```bash
cd simulator
py judge_simulator.py
```

## API Endpoints

| # | Endpoint | Method | Description |
|---|----------|--------|-------------|
| 1 | `/v1/healthz` | **GET** | Health check + context counts |
| 2 | `/v1/metadata` | **GET** | Team info |
| 3 | `/v1/context` | **POST** | Push context (idempotent by version) |
| 4 | `/v1/tick` | **POST** | Compose messages for triggers |
| 5 | `/v1/reply` | **POST** | Handle merchant/customer replies |

### 1. GET `/v1/healthz`

**Request:**
```bash
GET https://your-bot.ngrok-free.dev/v1/healthz
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "uptime_seconds": 3600,
  "contexts_loaded": {
    "category": 5,
    "merchant": 50,
    "customer": 200,
    "trigger": 100
  }
}
```

### 2. GET `/v1/metadata`

**Request:**
```bash
GET https://your-bot.ngrok-free.dev/v1/metadata
```

**Response (200 OK):**
```json
{
  "team_name": "Vera",
  "team_members": ["Mayank Maurya"],
  "model": "Groq Llama3-8B (cloud LLM, <2s response)",
  "approach": "4-Context Framework: Category + Merchant + Trigger + Customer contexts fed to LLM with few-shot examples",
  "contact_email": "hpmayankmaurya@gmail.com",
  "version": "1.1.0",
  "submitted_at": "2026-05-02T00:00:00Z"
}
```

### 3. POST `/v1/context`

**Request:**
```bash
POST https://your-bot.ngrok-free.dev/v1/context
Content-Type: application/json

{
  "scope": "merchant",
  "context_id": "m_001_drmeera_dentist_delhi",
  "version": 1,
  "payload": { "identity": {...}, "performance": {...}, "offers": [...] },
  "delivered_at": "2026-05-02T00:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "accepted": true,
  "ack_id": "ack_m_001_drmeera_dentist_delhi_v1",
  "stored_at": "2026-05-02T00:00:00.123Z"
}
```

**Response (409 Conflict - stale version):**
```json
{
  "accepted": false,
  "reason": "stale_version",
  "current_version": 1
}
```

### 4. POST `/v1/tick`

**Request:**
```bash
POST https://your-bot.ngrok-free.dev/v1/tick
Content-Type: application/json

{
  "now": "2026-05-02T00:00:00Z",
  "available_triggers": ["trg_001_research_digest_dentists"]
}
```

**Response (200 OK):**
```json
{
  "actions": [
    {
      "conversation_id": "conv_m_001_drmeera_dentist_delhi_trg_001_research_digest_dentists",
      "merchant_id": "m_001_drmeera_dentist_delhi",
      "customer_id": null,
      "send_as": "vera",
      "trigger_id": "trg_001_research_digest_dentists",
      "template_name": "vera_generic_v1",
      "template_params": [],
      "body": "Dr. Meera, JIDA's Oct issue landed...",
      "cta": "open_ended",
      "suppression_key": "research:dentists:2026-W17",
      "rationale": "Research digest with clinical anchor"
    }
  ]
}
```

**Note:** Max 20 actions per tick. Returns empty array if no messages to send.

### 5. POST `/v1/reply`

**Request:**
```bash
POST https://your-bot.ngrok-free.dev/v1/reply
Content-Type: application/json

{
  "conversation_id": "conv_001",
  "merchant_id": "m_001_drmeera_dentist_delhi",
  "customer_id": null,
  "from_role": "merchant",
  "message": "Yes, send me the abstract",
  "received_at": "2026-05-02T00:00:00Z",
  "turn_number": 2
}
```

**Response (200 OK) - Three valid actions:**

| Action | When |
|--------|------|
| `send` | Continue conversation, send next message |
| `wait` | Pause for N seconds (auto-reply detection) |
| `end` | Close conversation (hostility, repeated auto-replies) |

```json
{
  "action": "send",
  "body": "Sending now — also drafted a patient-ed WhatsApp...",
  "cta": "binary_yes_no",
  "wait_seconds": null,
  "rationale": "Honoring accept; adding next-best-step low-friction"
}
```

## Project Status

### ✅ Completed

- [x] 5 API endpoints (healthz, metadata, context, tick, reply)
- [x] 4-Context framework (Category, Merchant, Trigger, Customer)
- [x] Groq integration (llama3-8b, temperature=0, <2s response)
- [x] Idempotency (version-based, 409 for stale)
- [x] Multi-turn handling (auto-reply, hostility, intent)
- [x] Few-shot examples injection into LLM prompt
- [x] 20-action tick cap enforcement
- [x] Category-agnostic conversation manager
- [x] Full context prompt (signals, review themes, customer aggregate)
- [x] Dataset (50 merchants, 200 customers, 100 triggers)
- [x] Smoke tests (8/8 passing)
- [x] Public URL via ngrok

## Dataset

Every team starts from the same base data.

```
magicpin-ai-challenge/
├── challenge-brief.md
├── challenge-testing-brief.md
├── engagement-design.md
├── engagement-research.md
├── dataset/
│   ├── categories/         # 5 verticals: dentists, salons, restaurants, gyms, pharmacies
│   ├── merchants_seed.json   # 10 seeds → expanded to 50 merchants
│   ├── customers_seed.json   # 15 seeds → expanded to 200 customers
│   ├── triggers_seed.json    # 25 seeds → expanded to 100 triggers
│   └── generate_dataset.py   # deterministic expansion + 30 canonical test pairs
└── examples/
    ├── api-call-examples.md
    └── case-studies.md       # 10 judge-scored anchors
```

Generate the expanded dataset:
```bash
python3 dataset/generate_dataset.py --seed-dir dataset --out expanded
# →  expanded/  · 50 merchants · 200 customers · 100 triggers · 30 test pairs
```

Expanded dataset:
```
dataset/expanded/
├── categories/        # 5 categories
├── merchants/         # 50 merchants
├── customers/        # 200 customers
├── triggers/         # 100 triggers
└── test_pairs.json   # 30 canonical test pairs
```

## Files

```
src/
├── bot.py              # FastAPI (5 endpoints)
├── composer.py         # LLM composition with full context
├── context_store.py    # Context management (idempotent)
├── conversation.py     # Multi-turn handling
├── models.py          # Pydantic request/response models
├── config.py          # Configuration (.env loader)
└── prompts/
    ├── system_prompt.txt
    └── few_shot_examples.json

dataset/expanded/
├── categories/        # 5 categories
├── merchants/         # 50 merchants
├── customers/        # 200 customers
└── triggers/         # 100 triggers
```

## Key Features

1. **Fast** - Groq cloud LLM responds in <2 seconds
2. **Deterministic** - Temperature=0 for all LLM calls
3. **4-Context Framework** - Category + Merchant + Trigger + Customer
4. **Idempotent** - Version-based context acceptance (409 for stale)
5. **Multi-turn Intelligence** - Auto-reply/hostility/intent handling
6. **Category Voice** - Clinical (dentists), warm (salons), etc.
7. **Full Context** - Uses signals, review themes, customer aggregate, research digests
8. **Few-shot Examples** - 9 examples injected per trigger kind
9. **20-Action Cap** - Enforces spec max actions per tick

## Scoring Rubric

- **Decision Quality** (0-10): Pick best signal for moment
- **Specificity** (0-10): Use real numbers, dates, facts
- **Category Fit** (0-10): Match business type voice
- **Merchant Fit** (0-10): Personalize to merchant
- **Engagement** (0-10): Low-friction next action

## Submission

**Deadline:** 02 May 2026, 11:59 PM IST

**Requirements:**

- Public bot URL (e.g. https://xxxx.ngrok-free.dev)
- Bot must stay live for ~3 days after submission
- Handle new contexts judges inject
- Pass replay scenarios (auto-reply, intent, hostility)

## Notes

- Groq response time: <2s per composition
- In-memory storage (contexts lost on restart)
- Judge harness uses **fresh scenarios** (not the 30 test pairs)
- Bot scored on **grounding**, not pattern-matching
- Keep PC awake (disable sleep) or use a cloud host

## Contact

**Team:** Vera  
**Email:** hpmayankmaurya@gmail.com  
**Model:** Llama3-8B via Groq
