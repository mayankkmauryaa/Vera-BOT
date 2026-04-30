# MagicPin AI Challenge - Vera Bot

## Team: Team Alpha

**Model:** llama3 via Ollama (local)

## Quick Start

### 1. Install Ollama & Model

```bash
# Install Ollama: https://ollama.com
ollama serve
ollama pull llama3
```

### 2. Start Bot

```bash
cd F:\Projects\magicpin-ai-challenge
py -m uvicorn src.bot:app --host 0.0.0.0 --port 8080
```

### 3. Push Contexts

```bash
py push_contexts.py
```

### 4. Test

```bash
py run_all_tests.py
```

### 5. Run Judge

```bash
cd simulator
py judge_simulator.py
```

## Project Status

### ✅ Completed

- [x] 5 API endpoints (healthz, metadata, context, tick, reply)
- [x] 4-Context framework (Category, Merchant, Trigger, Customer)
- [x] Ollama integration (llama3, temperature=0)
- [x] Idempotency (version-based, 409 for stale)
- [x] Multi-turn handling (auto-reply, hostility, intent)
- [x] Judge simulator tests (ALL PASS)
- [x] Dataset (50 merchants, 200 customers, 100 triggers)
- [x] Documentation

### ❌ Pending

- [ ] Generate submission.jsonl (Ollama too slow locally)
- [ ] Host bot publicly (for judge harness)
- [ ] Full judge scoring (needs public URL)

## Files

```
src/
├── bot.py              # FastAPI (5 endpoints)
├── composer.py         # LLM composition
├── context_store.py    # Context management
├── conversation.py     # Multi-turn handling
├── models.py          # Pydantic models
├── config.py          # Configuration
└── prompts/
    ├── system_prompt.txt
    └── few_shot_examples.json

dataset/expanded/
├── categories/        # 5 categories
├── merchants/         # 50 merchants
├── customers/        # 200 customers
└── triggers/         # 100 triggers
```

## API Endpoints

| Endpoint       | Method | Description                   |
| -------------- | ------ | ----------------------------- |
| `/v1/healthz`  | GET    | Health check + context counts |
| `/v1/metadata` | GET    | Team info                     |
| `/v1/context`  | POST   | Push context (idempotent)     |
| `/v1/tick`     | POST   | Compose messages              |
| `/v1/reply`    | POST   | Handle replies                |

## Judge Results

```
✅ warmup - PASSED
✅ auto_reply - PASSED (Turn 1: send, Turn 2: wait, Turn 3: end)
✅ intent - PASSED (switches to action mode)
✅ hostile - PASSED (correctly ends)
```

## Key Features

1. **Deterministic** - Temperature=0 for all LLM calls
2. **4-Context Framework** - Category + Merchant + Trigger + Customer
3. **Idempotent** - Version-based context acceptance
4. **Multi-turn Intelligence** - Auto-reply/hostility/intent handling
5. **Category Voice** - Clinical (dentists), warm (salons), etc.
6. **Local LLM** - No API costs, works offline

## Scoring Rubric

- **Decision Quality** (0-10): Pick best signal for moment
- **Specificity** (0-10): Use real numbers, dates, facts
- **Category Fit** (0-10): Match business type voice
- **Merchant Fit** (0-10): Personalize to merchant
- **Engagement** (0-10): Low-friction next action

## Submission

**Deadline:** 02 May 2026, 11:59 PM IST

**Requirements:**

- Public bot URL (http://your-bot:8080)
- Bot must stay live for ~3 days after submission
- Handle new contexts judges inject
- Pass replay scenarios (auto-reply, intent, hostility)

## Notes

- Ollama response time: ~30s per composition
- In-memory storage (contexts lost on restart)
- Judge harness uses **fresh scenarios** (not the 30 test pairs)
- Bot scored on **grounding**, not pattern-matching

## Contact

**Team:** Team Alpha  
**Email:** [Your email]  
**Model:** llama3 via Ollama
