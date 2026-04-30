import requests
import json
import re
from typing import Optional, Dict, Any
from src.config import GEMINI_API_KEY, GEMINI_MODEL, OPENAI_API_KEY, OPENAI_MODEL, OLLAMA_URL, OLLAMA_MODEL


class Composer:
    def __init__(self):
        self.few_shot = self._load_few_shot()
        self.system_prompt = self._load_system_prompt()
        # API keys
        self.gemini_api_key = GEMINI_API_KEY
        self.openai_api_key = OPENAI_API_KEY
        # Models
        self.gemini_models = [GEMINI_MODEL, "gemini-1.5-flash", "gemini-pro-latest"]
        self.openai_model = OPENAI_MODEL
        self.ollama_url = OLLAMA_URL
        self.ollama_model = OLLAMA_MODEL
        
    def compose(self, category: Dict[str, Any], merchant: Dict[str, Any], 
                trigger: Dict[str, Any], customer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        send_as = "merchant_on_behalf" if customer else "vera"
        
        prompt = self._build_prompt(category, merchant, trigger, customer)
        system = self.system_prompt
        
        # Try Gemini models first
        for model in self.gemini_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
                payload = {
                    "contents": [{
                        "parts": [{"text": f"{system}\n\n{prompt}"}]
                    }],
                    "generationConfig": {
                        "temperature": 0,
                        "maxOutputTokens": 200
                    }
                }
                
                response = requests.post(url, json=payload, timeout=15)
                response.raise_for_status()
                data = response.json()
                llm_response = data["candidates"][0]["content"]["parts"][0]["text"]
                
                result = self._extract_json(llm_response)
                
                return {
                    "body": result.get("body", ""),
                    "cta": result.get("cta", "open_ended"),
                    "send_as": result.get("send_as", send_as),
                    "suppression_key": result.get("suppression_key", trigger.get("suppression_key", "")),
                    "rationale": result.get("rationale", "")
                }
            except Exception as e:
                print(f"Gemini {model} failed: {e}")
                continue
        
        # Fallback to OpenAI
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0,
                "max_tokens": 200
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            llm_response = response.json()["choices"][0]["message"]["content"]
            
            result = self._extract_json(llm_response)
            
            return {
                "body": result.get("body", ""),
                "cta": result.get("cta", "open_ended"),
                "send_as": result.get("send_as", send_as),
                "suppression_key": result.get("suppression_key", trigger.get("suppression_key", "")),
                "rationale": result.get("rationale", "")
            }
        except Exception as e:
            print(f"OpenAI failed: {e}")
        
        # Final fallback to Ollama
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
            print(f"Composer error (all LLMs failed): {e}")
            owner = merchant.get("identity", {}).get("owner_first_name", "there")
            return {
                "body": f"Hi {owner}, quick update coming shortly.",
                "cta": "none",
                "send_as": send_as,
                "suppression_key": trigger.get("suppression_key", ""),
                "rationale": "Fallback due to composition error"
            }
            payload = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0,
                "max_tokens": 200
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            llm_response = response.json()["choices"][0]["message"]["content"]
            
            result = self._extract_json(llm_response)
            
            return {
                "body": result.get("body", ""),
                "cta": result.get("cta", "open_ended"),
                "send_as": result.get("send_as", send_as),
                "suppression_key": result.get("suppression_key", trigger.get("suppression_key", "")),
                "rationale": result.get("rationale", "")
            }
            
        except Exception as e:
            print(f"OpenAI error: {e}")
            
        # Fallback to Ollama
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
            print(f"Composer error (all LLMs failed): {e}")
            owner = merchant.get("identity", {}).get("owner_first_name", "there")
            return {
                "body": f"Hi {owner}, quick update coming shortly.",
                "cta": "none",
                "send_as": send_as,
                "suppression_key": trigger.get("suppression_key", ""),
                "rationale": "Fallback due to composition error"
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
    
    def _load_few_shot(self) -> Dict[str, Any]:
        try:
            with open("src/prompts/few_shot_examples.json", "r") as f:
                return json.load(f)
        except:
            return {}
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return {}
