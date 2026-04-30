from typing import Dict, Any, Optional, Tuple
from datetime import datetime


class ContextStore:
    def __init__(self):
        self._contexts: Dict[Tuple[str, str], Dict[str, Any]] = {}
    
    def push_context(self, scope: str, context_id: str, version: int, 
                    payload: Dict[str, Any], delivered_at: str) -> Dict[str, Any]:
        key = (scope, context_id)
        current = self._contexts.get(key)
        
        if current and current["version"] >= version:
            return {
                "accepted": False,
                "reason": "stale_version",
                "current_version": current["version"]
            }
        
        self._contexts[key] = {
            "version": version,
            "payload": payload,
            "stored_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "accepted": True,
            "ack_id": f"ack_{context_id}_v{version}",
            "stored_at": self._contexts[key]["stored_at"]
        }
    
    def get_context(self, scope: str, context_id: str) -> Optional[Dict[str, Any]]:
        key = (scope, context_id)
        entry = self._contexts.get(key)
        return entry["payload"] if entry else None
    
    def get_contexts_by_scope(self, scope: str) -> Dict[str, Dict[str, Any]]:
        return {
            ctx_id: entry["payload"] 
            for (scp, ctx_id), entry in self._contexts.items() 
            if scp == scope
        }
    
    def get_counts(self) -> Dict[str, int]:
        counts = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
        for (scope, _) in self._contexts:
            if scope in counts:
                counts[scope] += 1
        return counts
    
    def get_merchant_category(self, merchant_id: str) -> Optional[Dict[str, Any]]:
        merchant = self.get_context("merchant", merchant_id)
        if not merchant:
            return None
        category_slug = merchant.get("category_slug")
        if not category_slug:
            return None
        return self.get_context("category", category_slug)
