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

```bash
cp .env.example .env         # add GROQ_API_KEY
py -m uvicorn src.bot:app --host 0.0.0.0 --port 8080
```

## 4-Context Framework

Every composition uses all available contexts:

| Context | Role |
|---------|------|
| **Category** | Voice/tone, peer stats, research digest, patient content library |
| **Merchant** | Identity, performance, subscription, signals, review themes |
| **Trigger** | Kind, urgency, payload with actionable details |
| **Customer** | Relationship state, preferences, consent scope (when applicable) |

## Conversation Handling

The bot handles three reply patterns:

| Pattern | Detection | Action |
|---------|-----------|--------|
| Normal reply | Engaged merchant message | `send` — continue with next-best-step |
| Auto-reply | Canned/wall-of-text response | `wait` → detect repeats → `end` |
| Hostile/off-topic | Abuse or unrelated question | Polite deflection → `end` |

## Scoring

| Dimension | Description |
|-----------|-------------|
| Decision Quality | Pick the best signal for the moment |
| Specificity | Use real numbers, dates, facts from context |
| Category Fit | Match business-type voice (clinical, warm, energetic) |
| Merchant Fit | Personalize to merchant's actual data |
| Engagement | Low-friction next action, curiosity-driven |

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
