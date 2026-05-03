import re
import os
import json
from typing import Dict, Any, Optional

class ConversationManager:
    def __init__(self, context_store=None, llm_api_key=None, llm_model="llama-3.1-8b-instant"):
        self.conversations: Dict[str, list] = {}
        self.auto_reply_tracker: Dict[str, int] = {}
        self.conversation_context: Dict[str, dict] = {}
        self.context_store = context_store
        self.llm_api_key = llm_api_key or os.getenv("GROQ_API_KEY", "")
        self.llm_model = llm_model
        
        # Load prompts
        self.system_prompt = self._load_system_prompt()
        self.few_shot_examples = self._load_few_shot_examples()

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

        # Use LLM for contextual reply
        return self._generate_llm_reply(conv_id, message, from_role)

    def _generate_llm_reply(self, conv_id: str, message: str, from_role: str) -> Dict[str, Any]:
        """Generate contextual reply using LLM with conversation history + context."""
        context = self.conversation_context.get(conv_id, {})
        merchant = context.get("merchant", {})
        customer = context.get("customer", {})
        history = self.conversations.get(conv_id, [])

        # Build prompt using system_prompt + few_shot examples
        prompt_parts = [self.system_prompt.rstrip('\n')]

        # Add few-shot examples for replies
        prompt_parts.append("\n=== RELEVANT FEW-SHOT EXAMPLES (Replies) ===")
        reply_examples = self.few_shot_examples.get("reply", [])
        if reply_examples:
            for ex in reply_examples[:2]:
                output = ex.get("output", {})
                prompt_parts.append(f"Example: {output.get('body', '')}")
        else:
            prompt_parts.append("(No specific reply examples)")

        # Add current context
        prompt_parts.append("\n=== CURRENT CONVERSATION ===")
        prompt_parts.append(f"Merchant: {json.dumps(merchant, indent=2) if merchant else '{}'}")
        prompt_parts.append(f"Customer: {json.dumps(customer, indent=2) if customer else '{}'}")
        
        prompt_parts.append("\n=== HISTORY ===")
        for msg in history:
            prompt_parts.append(f"{msg['from']}: {msg['msg']}")
        
        prompt_parts.append(f"\n=== CURRENT MESSAGE ===")
        prompt_parts.append(f"From: {from_role}")
        prompt_parts.append(f"Message: {message}")
        
        prompt_parts.append("\n=== YOUR TASK ===")
        prompt_parts.append("Generate a WhatsApp reply as Vera. Rules:")
        prompt_parts.append("1. Use merchant's name correctly")
        prompt_parts.append("2. Be specific with any numbers/dates in context")
        prompt_parts.append("3. Use 1+ engagement levers (loss aversion, social proof, effort externalization)")
        prompt_parts.append("4. Single clear CTA at end (prefer binary_yes_no)")
        prompt_parts.append("5. Keep under 160 chars (WhatsApp-length)")
        prompt_parts.append("\nReturn ONLY valid JSON:")
        prompt_parts.append('{"action": "send", "body": "...", "cta": "binary_yes_no|open_ended|multi_choice_slot", "rationale": "..."}')

        prompt = "\n".join(prompt_parts)

        # Call LLM
        try:
            import requests
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={
                    "model": self.llm_model,
                    "messages": [
                        {"role": "system", "content": "You are Vera, merchant AI assistant. Generate contextual WhatsApp replies."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0,
                    "max_tokens": 200
                },
                headers={"Authorization": f"Bearer {self.llm_api_key}", "Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            llm_response = response.json()["choices"][0]["message"]["content"]

            # Extract JSON from LLM response
            import re
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "action": "send",
                    "body": result.get("body", f"Got it! I'm on it, {merchant.get('identity', {}).get('name', 'there')}."),
                    "cta": result.get("cta", "open_ended"),
                    "rationale": result.get("rationale", "LLM-generated contextual reply")
                }

        except Exception as e:
            print(f"LLM reply error: {e}")

        # Fallback: Use rule-based if LLM fails
        return self._fallback_reply(conv_id, message, merchant)

    def _fallback_reply(self, conv_id: str, message: str, merchant: dict) -> Dict[str, Any]:
        """Fallback rule-based reply if LLM fails."""
        context = self.conversation_context.get(conv_id, {})
        merchant = context.get("merchant", {})
        merchant_name = merchant.get("identity", {}).get("name", "there") if merchant else "there"
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["book", "appointment", "schedule"]):
            return {
                "action": "send",
                "body": f"Great {merchant_name}! I can help you book that. What date and time works best for you?",
                "cta": "open_ended",
                "rationale": "Booking query - asking for details"
            }

        if any(word in msg_lower for word in ["x-ray", "radiograph", "dose", "film"]):
            return {
                "action": "send",
                "body": f"{merchant_name}, I'll help you audit your X-ray setup for compliance. What unit model and film type are you currently using?",
                "cta": "open_ended",
                "rationale": "X-ray compliance query"
            }

        return {
            "action": "send",
            "body": f"Got it {merchant_name}! I'm working on that for you. Is there anything specific you'd like me to focus on?",
            "cta": "open_ended",
            "rationale": "Generic follow-up"
        }

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
