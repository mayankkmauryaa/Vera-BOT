from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ContextPushRequest(BaseModel):
    scope: str  # "category" | "merchant" | "customer" | "trigger"
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: str


class TickRequest(BaseModel):
    now: str
    available_triggers: List[str] = []


class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str
    message: str
    received_at: str
    turn_number: int


class Action(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    send_as: str  # "vera" | "merchant_on_behalf"
    trigger_id: Optional[str] = None
    template_name: Optional[str] = None
    template_params: List[str] = []
    body: str
    cta: str  # "binary_yes_no" | "open_ended" | "multi_choice_slot" | "none"
    suppression_key: str
    rationale: str


class TickResponse(BaseModel):
    actions: List[Action] = []


class ReplyResponse(BaseModel):
    action: str  # "send" | "wait" | "end"
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: Optional[str] = None


class HealthzResponse(BaseModel):
    status: str
    uptime_seconds: int
    contexts_loaded: Dict[str, int]


class MetadataResponse(BaseModel):
    team_name: str
    team_members: List[str]
    model: str
    approach: str
    contact_email: str
    version: str
    submitted_at: str


class ContextPushResponse(BaseModel):
    accepted: bool
    reason: Optional[str] = None
    current_version: Optional[int] = None
    ack_id: Optional[str] = None
    stored_at: Optional[str] = None
