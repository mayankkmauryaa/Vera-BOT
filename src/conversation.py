import re
import json
from typing import Dict, Any, Optional


class ConversationManager:
    def __init__(self, context_store=None):
        self.conversations: Dict[str, list] = {}
        self.auto_reply_tracker: Dict[str, int] = {}
        self.conversation_context: Dict[str, dict] = {}
        self.context_store = context_store

        self.auto_reply_patterns = [
            r"thank you for contacting",
            r"our team will respond",
            r"auto.*reply",
            r"thank you.*team.*respond"
        ]

        self.hostile_patterns = [
            "stop", "stop messaging", "not interested", "useless",
            "spam", "bothering", "stop sending", "no thanks",
            "don't message", "unsubscribe", "remove me"
        ]

        self.intent_patterns = [
            "ok let's do it", "yes let's", "go ahead",
            "proceed", "send it", "do it", "yes please",
            "ok lets do it", "yes, send", "sure, go ahead",
            "yes", "sure", "ok", "okay", "yep", "yeah",
            "sounds good", "that works", "interested"
        ]

        self.off_topic_patterns = [
            "gst", "filing", "tax", "website", "seo"
        ]

    def handle_reply(self, conv_id: str, merchant_id: Optional[str],
                    customer_id: Optional[str], message: str,
                    turn_number: int, from_role: str = "merchant") -> Dict[str, Any]:

        self.conversations.setdefault(conv_id, []).append({
            "from": from_role,
            "msg": message,
            "turn": turn_number
        })

        # Store context for this conversation
        if merchant_id and merchant_id not in self.conversation_context:
            self.conversation_context[conv_id] = {
                "merchant_id": merchant_id,
                "customer_id": customer_id,
                "merchant": None,
                "customer": None,
                "trigger": None
            }
            # Try to load merchant context
            if self.context_store:
                self.conversation_context[conv_id]["merchant"] = self.context_store.get_context("merchant", merchant_id)
                if customer_id:
                    self.conversation_context[conv_id]["customer"] = self.context_store.get_context("customer", customer_id)

        if from_role == "merchant":
            if self._is_auto_reply(message):
                track_key = merchant_id if merchant_id else conv_id
                return self._handle_auto_reply(track_key)

            if self._is_hostile(message):
                return self._handle_hostile(conv_id)

            if self._is_intent(message):
                return self._handle_intent(conv_id)

            if self._is_off_topic(message):
                return self._handle_off_topic(conv_id)

        return {
            "action": "send",
            "body": self._generate_contextual_reply(conv_id, message),
            "cta": "open_ended",
            "rationale": "Processing merchant's specific inquiry"
        }

    def _generate_contextual_reply(self, conv_id: str, message: str) -> str:
        """Generate contextual reply based on conversation history and stored context."""
        history = self.conversations.get(conv_id, [])
        msg_lower = message.lower()
        context = self.conversation_context.get(conv_id, {})
        merchant = context.get("merchant", {})
        merchant_name = merchant.get("identity", {}).get("name", "there") if merchant else "there"

        # Check for booking-related queries
        if any(word in msg_lower for word in ["book", "appointment", "schedule", "slot"]):
            return f"Great {merchant_name}! I can help you book that. What date and time works best for you?"

        # Check for X-ray/equipment queries
        if any(word in msg_lower for word in ["x-ray", "radiograph", "dose", "film", "equipment"]):
            return f"{merchant_name}, I'll help you audit your X-ray setup for DCI compliance. What unit model and film type are you currently using?"

        # Check for help requests
        if any(word in msg_lower for word in ["help", "how", "what", "why"]):
            return f"I'm here to help {merchant_name}! Could you tell me more about what you need assistance with?"

        # Check for day mentions (scheduling)
        if any(day in msg_lower for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]):
            return f"Perfect! I've noted your preferred day. What time would you prefer - morning, afternoon, or evening?"

        # Check for time mentions
        if any(word in msg_lower for word in ["am", "pm", "morning", "evening", "afternoon"]):
            return f"Noted! I'll schedule that for you. Should I send you a confirmation message to share with the customer?"

        # If conversation has multiple exchanges, be more specific
        if len(history) > 2:
            return f"Thanks for the details {merchant_name}! Let me prepare everything for you. Anything else you'd like me to include?"

        # Default contextual response
        return f"Got it {merchant_name}! I'm working on that for you. Is there anything specific you'd like me to focus on?"

    def _is_auto_reply(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(re.search(p, msg_lower) for p in self.auto_reply_patterns)

    def _handle_auto_reply(self, track_key: str) -> Dict[str, Any]:
        self.auto_reply_tracker[track_key] = self.auto_reply_tracker.get(track_key, 0) + 1
        count = self.auto_reply_tracker[track_key]

        print(f"[AUTO-REPLY] track_key={track_key}, count={count}", flush=True)

        if count == 1:
            return {
                "action": "send",
                "body": "Looks like an auto-reply. When you see this, just reply 'Yes' for the info.",
                "cta": "binary_yes_no",
                "rationale": "Detected auto-reply; prompting owner to reply"
            }
        elif count == 2:
            return {
                "action": "wait",
                "wait_seconds": 14400,
                "rationale": f"Auto-reply {count}x; waiting for owner"
            }
        else:
            return {
                "action": "end",
                "rationale": f"Auto-reply {count}x; closing conversation"
            }

    def _is_hostile(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(p in msg_lower for p in self.hostile_patterns)

    def _handle_hostile(self, conv_id: str) -> Dict[str, Any]:
        return {
            "action": "end",
            "rationale": "Merchant explicitly wants to stop. Closing gracefully."
        }

    def _is_intent(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(p in msg_lower for p in self.intent_patterns)

    def _handle_intent(self, conv_id: str) -> Dict[str, Any]:
        return {
            "action": "send",
            "body": "Perfect! I'll get this set up for you right away. Want me to send you a preview first?",
            "cta": "binary_yes_no",
            "rationale": "Merchant committed; switching to action mode with low-friction confirmation"
        }

    def _is_off_topic(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(p in msg_lower for p in self.off_topic_patterns)

    def _handle_off_topic(self, conv_id: str) -> Dict[str, Any]:
        return {
            "action": "send",
            "body": "I'll leave that to your specialist. Back to our topic...",
            "cta": "open_ended",
            "rationale": "Out-of-scope redirected gracefully"
        }
