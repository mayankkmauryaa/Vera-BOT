import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.config import *
from src.models import *
from src.context_store import ContextStore
from src.composer import Composer
from src.conversation import ConversationManager

MAX_ACTIONS_PER_TICK = 20

app = FastAPI(title="Vera AI Challenge Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
START_TIME = time.time()

context_store = ContextStore()
composer = Composer()
conv_manager = ConversationManager(context_store)


@app.get("/v1/healthz", response_model=HealthzResponse)
async def healthz():
    counts = context_store.get_counts()
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
        "contexts_loaded": counts
    }


@app.get("/v1/metadata", response_model=MetadataResponse)
async def metadata():
    return {
        "team_name": TEAM_NAME,
        "team_members": TEAM_MEMBERS,
        "model": MODEL_DESCRIPTION,
        "approach": APPROACH,
        "contact_email": CONTACT_EMAIL,
        "version": VERSION,
        "submitted_at": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/v1/context")
async def push_context(body: ContextPushRequest):
    result = context_store.push_context(
        body.scope, body.context_id, body.version,
        body.payload, body.delivered_at
    )
    if not result["accepted"]:
        raise HTTPException(status_code=409, detail=result)
    return result


@app.post("/v1/tick", response_model=TickResponse)
async def tick(body: TickRequest):
    actions = []

    for trg_id in body.available_triggers:
        if len(actions) >= MAX_ACTIONS_PER_TICK:
            break

        trigger = context_store.get_context("trigger", trg_id)
        if not trigger:
            continue

        merchant_id = trigger.get("merchant_id")
        merchant = context_store.get_context("merchant", merchant_id)
        if not merchant:
            continue

        category_slug = merchant.get("identity", {}).get("category_slug")
        if not category_slug:
            continue
        category = context_store.get_context("category", category_slug)
        if not category:
            continue

        customer = None
        customer_id = trigger.get("customer_id")
        if customer_id:
            customer = context_store.get_context("customer", customer_id)

        try:
            result = composer.compose(category, merchant, trigger, customer)
            actions.append({
                "conversation_id": f"conv_{merchant_id}_{trg_id}",
                "merchant_id": merchant_id,
                "customer_id": customer_id,
                "send_as": result["send_as"],
                "trigger_id": trg_id,
                "template_name": "vera_generic_v1",
                "template_params": [],
                "body": result["body"],
                "cta": result["cta"],
                "suppression_key": result["suppression_key"],
                "rationale": result["rationale"]
            })
        except Exception as e:
            print(f"Compose error for {trg_id}: {e}")

    return {"actions": actions}


@app.post("/v1/reply", response_model=ReplyResponse)
async def reply(body: ReplyRequest):
    print(f"[DEBUG] Reply: conv_id={body.conversation_id}, turn={body.turn_number}, from_role={body.from_role}, msg={body.message[:50]}...", flush=True)
    result = conv_manager.handle_reply(
        body.conversation_id, body.merchant_id, body.customer_id,
        body.message, body.turn_number, body.from_role
    )
    print(f"[DEBUG] Reply result: {result}", flush=True)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BOT_HOST, port=BOT_PORT)
