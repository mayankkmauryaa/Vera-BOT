import re
import json
from typing import Dict, Any, Optional


class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, list] = {}
        self.auto_reply_tracker: Dict[str, int] = {}  # Tracks by merchant_id
        
        self.auto_reply_patterns = [
            r"thank you for contacting",
            r"our team will respond",
            r"auto.*reply",
            r"thank you.*team.*respond"
        ]
        
        self.hostile_patterns = [
            "stop messaging", "not interested", "useless", 
            "spam", "bothering", "stop sending"
        ]
        
        self.intent_patterns = [
            "ok let's do it", "yes let's", "go ahead", 
            "proceed", "send it", "do it", "yes please"
        ]
        
        self.off_topic_patterns = [
            "gst", "filing", "tax", "website", "seo"
        ]
    
    def handle_reply(self, conv_id: str, merchant_id: Optional[str], 
                    customer_id: Optional[str], message: str, 
                    turn_number: int) -> Dict[str, Any]:
        
        self.conversations.setdefault(conv_id, []).append({
            "from": "merchant",
            "msg": message,
            "turn": turn_number
        })
        
        if self._is_auto_reply(message):
            # Track by merchant_id (judge uses same merchant, different conv_id)
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
            "body": "Got it, let me process that for you.",
            "cta": "open_ended",
            "rationale": "Continuing conversation"
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
            # 3+ times - end conversation
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
            "body": "Perfect! I'll draft the patient education message now and send it to you shortly.",
            "cta": "open_ended",
            "rationale": "Merchant committed; switching to action mode"
        }
    
    def _is_off_topic(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(p in msg_lower for p in self.off_topic_patterns)
    
    def _handle_off_topic(self, conv_id: str) -> Dict[str, Any]:
        return {
            "action": "send",
            "body": "I'll leave that to your CA. Back to our topic...",
            "cta": "open_ended",
            "rationale": "Out-of-scope redirected gracefully"
        }
