import requests
import json
import re
from typing import Optional, Dict, Any
from src.config import OLLAMA_URL, OLLAMA_MODEL


class Composer:
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        self.ollama_url = OLLAMA_URL
        self.ollama_model = OLLAMA_MODEL
        
    def compose(self, category: Dict[str, Any], merchant: Dict[str, Any], 
                trigger: Dict[str, Any], customer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        send_as = "merchant_on_behalf" if customer else "vera"
        
        prompt = self._build_prompt(category, merchant, trigger, customer)
        system = self.system_prompt
        
        # Use Ollama only
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": f"{system}\n\n{prompt}",
                    "stream": False,
                    "options": {"temperature": 0, "num_predict": 150}
                },
                timeout=90
            )
            response.raise_for_status()
            llm_response = response.json()["response"]
            
            result = self._extract_json(llm_response)
            
            return {
                "body": result.get("body", ""),
                "cta": result.get("cta", "open_ended"),
                "send_as": result.get("send_as", send_as),
                "suppression_key": result.get("suppression_key", trigger.get("suppression_key", "")),
                "rationale": result.get("rationale", "")
            }
        except Exception as e:
            print(f"Ollama error: {e}")
            owner = merchant.get("identity", {}).get("owner_first_name", "there")
            return {
                "body": f"Hi {owner}, quick update coming shortly.",
                "cta": "none",
                "send_as": send_as,
                "suppression_key": trigger.get("suppression_key", ""),
                "rationale": "Fallback due to Ollama error"
            }
    
    def _build_prompt(self, category, merchant, trigger, customer) -> str:
        prompt = "CONTEXT:\n"
        
        # Category context (simplified)
        voice = category.get("voice", {})
        prompt += f"Category: {category.get('slug', '')}, Voice: {voice.get('tone', '')}\n"
        prompt += f"Allowed: {', '.join(voice.get('vocab_allowed', [])[:5])}\n"
        
        # Merchant context (simplified)
        identity = merchant.get("identity", {})
        prompt += f"Merchant: {identity.get('name', '')}, Owner: {identity.get('owner_first_name', '')}\n"
        
        perf = merchant.get("performance", {})
        prompt += f"Views: {perf.get('views', 0)}, Calls: {perf.get('calls', 0)}\n"
        
        offers = merchant.get("offers", [])
        active = [o["title"] for o in offers if o.get("status") == "active"]
        if active:
            prompt += f"Offers: {', '.join(active[:2])}\n"
        
        # Trigger context
        prompt += f"\nTrigger: {trigger.get('kind', '')}\n"
        
        # Add research digest if available
        if trigger.get("kind") == "research_digest":
            digest = category.get("digest", [])
            if digest:
                item = digest[0]
                prompt += f"Research: {item.get('headline', '')}\n"
        
        # Customer context (simplified)
        if customer:
            cust_id = customer.get("identity", {})
            prompt += f"\nCustomer: {cust_id.get('name', '')}, State: {customer.get('state', '')}\n"
        
        prompt += "\nReturn JSON: {\"body\": \"message\", \"cta\": \"choice\", \"send_as\": \"vera\", \"rationale\": \"reason\"}\n"
        
        return prompt
    
    def _load_system_prompt(self) -> str:
        try:
            with open("src/prompts/system_prompt.txt", "r") as f:
                return f.read()
        except:
            return "You are Vera, a merchant AI assistant. Compose WhatsApp messages using the 4-context framework."
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return {}
