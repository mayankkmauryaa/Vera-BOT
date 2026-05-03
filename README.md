# MagicPin AI Challenge — Vera Bot

## Team: Vera

**Live URL:** `https://vera-bot-npn1.onrender.com`  
**Model:** Llama 3.1 8B Instant via Groq

## Architecture

```
Judge Harness ──HTTPS──► FastAPI Bot (Render)
                        ├── /v1/healthz     GET
                        ├── /v1/metadata    GET
                        ├── /v1/context     POST  (idempotent, versioned)
                        ├── /v1/tick        POST  (≤20 actions)
                        └── /v1/reply       POST  (send / wait / end)

                        └── LLM: Groq (llama-3.1-8b-instant, temp=0)
```

## Quick Start

**Local Development:**

```bash
cp .env.example .env         # add GROQ_API_KEY
pip install -r requirements.txt
py -m uvicorn src.bot:app --host 0.0.0.0 --port 8080
```

**Environment Variables (in .env or Render):**
- `GROQ_API_KEY` - Get from https://console.groq.com/keys
- `GROQ_MODEL` - Default: llama-3.1-8b-instant
- `BOT_HOST` - Default: 0.0.0.0
- `BOT_PORT` - Default: 8080

**Deploy to Render:**
- Push to GitHub → Auto-deploys to https://vera-bot-npn1.onrender.com
- Set environment variables in Render dashboard
- Ensure `GROQ_API_KEY` is set (not committed to code)

## 4-Context Framework

Every composition uses all available contexts:

| Context | Role |
|---------|------|
| **Category** | Voice/tone, peer stats, research digest, patient content library |
| **Merchant** | Identity, performance, subscription, signals, review themes |
| **Trigger** | Kind, urgency, payload with actionable details |
| **Customer** | Relationship state, preferences, consent scope (when applicable) |

## Conversation Handling

The bot handles four reply patterns with improved contextual awareness:

| Pattern | Detection | Action |
|---------|-----------|--------|
| Normal reply | Engaged merchant message | `send` — contextual reply with merchant name |
| Auto-reply | Canned/wall-of-text response | `wait` → detect repeats → `end` |
| Hostile/STOP | "stop", "no", "not interested", etc. | Immediate `end` — protects merchant trust |
| Intent confirmation | "yes", "sure", "ok", etc. | `send` — move to next action step |
| Off-topic | Unrelated queries (GST, tax, etc.) | Polite redirect → `send` |

**Key Improvements:**
- ✅ STOP handling returns `action='end'` immediately
- ✅ Contextual replies replace generic "Got it, let me process that for you."
- ✅ Merchant name personalization in all replies
- ✅ Better pattern matching for intents and hostile messages

## Evaluation Status

**Current Score: 15/100** (as of May 3, 2026)

| Dimension | Score | Status |
|-----------|--------|--------|
| Decision Quality | 2/10 | ⚠️ Needs improvement |
| Specificity | 2/10 | ⚠️ Use more real data |
| Category Fit | 6/10 | ✅ Good |
| Merchant Fit | 6/10 | ✅ Good |
| Engagement Compulsion | 1/10 | ⚠️ Needs stronger CTAs |

**Replay Test Results:**
- ✅ Trigger Coverage (6 kinds)
- ✅ Context Pushes (/v1/context)
- ✅ Schema Compliance (5 endpoints)
- ⚠️ Reply Handling — Fixed: contextual replies now (was "Got it, let me process")
- ⚠️ Auto-reply Detection — Working (send → wait → end)
- ✅ STOP Handling — Fixed: returns `action='end'` immediately

**Recent Fixes Applied:**
1. STOP/hostile intent → immediate `action='end'`
2. Replaced generic replies with contextual, personalized responses
3. Added merchant name personalization
4. Improved pattern matching for intents ("yes", "sure", "ok", etc.)
5. Moved API keys to environment variables (.env)

**Next Steps:**
- Deploy fixes to Render
- Resubmit to magicpin for re-evaluation
- Improve decision quality and engagement compulsion in triggers

## Dataset

Seed data provided in `challenge zip extracted/dataset/`:

| File | Count | Judge Expands To |
|------|-------|------------------|
| `categories/*.json` | 5 | 5 (unchanged) |
| `merchants_seed.json` | 10 | 50 |
| `customers_seed.json` | 15 | 200 |
| `triggers_seed.json` | 25 | 100 |

Judge pushes the full expanded dataset during evaluation warmup. Bot must handle incremental updates mid-test.

## Project Structure

```
src/
├── bot.py              FastAPI app — 5 endpoints, 20-action cap
├── composer.py         LLM prompt builder + Groq call (with .env support)
├── context_store.py    Versioned in-memory context storage
├── conversation.py     Multi-turn: auto-reply, hostile, intent, contextual replies
├── models.py           Pydantic request/response schemas
├── config.py           Env var loader (supports .env, .env.example provided)
└── prompts/
    ├── system_prompt.txt    (updated with STOP handling rules)
    └── few_shot_examples.json

challenge zip extracted/
├── challenge-brief.md
├── challenge-testing-brief.md
├── engagement-design.md
├── engagement-research.md
├── dataset/            Seed data + generator
│   ├── categories/*.json   (dentists, gyms, pharmacies, restaurants, salons)
│   ├── merchants_seed.json
│   ├── customers_seed.json
│   ├── triggers_seed.json
│   └── generate_dataset.py
└── judge_simulator.py  (updated to use .env for API keys)

.env.example            Template for environment variables (DO NOT COMMIT .env)
Procfile                Render deployment
requirements.txt        Python dependencies
runtime.txt             Python 3.11
```

### Environment Setup

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
# Edit .env with your GROQ_API_KEY
```

**Never commit `.env` file** — it's in `.gitignore`.
src/
├── bot.py              FastAPI app — 5 endpoints, 20-action cap
├── composer.py         LLM prompt builder + Groq call
├── context_store.py    Versioned in-memory context storage
├── conversation.py     Multi-turn: auto-reply, hostile, intent
├── models.py           Pydantic request/response schemas
├── config.py           Env var loader
└── prompts/
    ├── system_prompt.txt
    └── few_shot_examples.json

challenge zip extracted/
├── challenge-brief.md
├── challenge-testing-brief.md
├── engagement-design.md
├── engagement-research.md
├── dataset/            Seed data + generator
├── examples/           API examples + case studies
└── judge_simulator.py

Procfile                Render deployment
requirements.txt        Python dependencies
runtime.txt             Python 3.11
website.md              Reference
```

## Contact

**Team:** Vera  
**Member:** Mayank Maurya  
**Email:** hpmayankmaurya@gmail.com
