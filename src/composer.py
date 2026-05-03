import requests
import json
import re
import os
from typing import Optional, Dict, Any, List
from src.config import GROQ_API_KEY, GROQ_MODEL


class Composer:
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        self.few_shot_examples = self._load_few_shot_examples()
        self.groq_api_key = GROQ_API_KEY
        self.groq_model = GROQ_MODEL

    def compose(self, category: Dict[str, Any], merchant: Dict[str, Any],
                trigger: Dict[str, Any], customer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        send_as = "merchant_on_behalf" if customer else "vera"

        prompt = self._build_prompt(category, merchant, trigger, customer)
        system = self.system_prompt

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={
                    "model": self.groq_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0,
                    "max_tokens": 300
                },
                headers={"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            llm_response = response.json()["choices"][0]["message"]["content"]

            result = self._extract_json(llm_response)

            # Validate response has required specificity
            body = result.get("body", "")
            if not self._validate_specificity(body):
                print(f"WARNING: Low specificity in LLM response: {body[:100]}...")

            return {
                "body": result.get("body", ""),
                "cta": result.get("cta", "open_ended"),
                "send_as": result.get("send_as", send_as),
                "suppression_key": result.get("suppression_key", trigger.get("suppression_key", "")),
                "rationale": result.get("rationale", "")
            }
        except Exception as e:
            print(f"Groq error: {e}")
            owner = merchant.get("identity", {}).get("owner_first_name", "there")
            return {
                "body": f"Hi {owner}, quick update coming shortly.",
                "cta": "none",
                "send_as": send_as,
                "suppression_key": trigger.get("suppression_key", ""),
                "rationale": "Fallback due to Groq error"
            }

    def _build_prompt(self, category, merchant, trigger, customer) -> str:
        parts = []

        parts.append("=== CATEGORY CONTEXT ===")
        parts.append(f"Slug: {category.get('slug', '')}")
        voice = category.get("voice", {})
        parts.append(f"Tone: {voice.get('tone', '')}")
        parts.append(f"Register: {voice.get('register', '')}")
        parts.append(f"Code-mix: {voice.get('code_mix', '')}")
        parts.append(f"Vocab allowed: {', '.join(voice.get('vocab_allowed', [])[:8])}")
        parts.append(f"Vocab taboo: {', '.join(voice.get('vocab_taboo', [])[:5])}")

        digest = category.get("digest", [])
        if digest:
            parts.append("\n--- Research Digest Items ---")
            for item in digest[:3]:
                parts.append(f"  [{item.get('id', '')}] {item.get('title', '')}")
                parts.append(f"    Source: {item.get('source', '')}")
                parts.append(f"    Summary: {item.get('summary', '')}")
                if item.get('actionable'):
                    parts.append(f"    Actionable: {item['actionable']}")
                parts.append("")

        seasonal = category.get("seasonal_beats", [])
        if seasonal:
            parts.append("--- Seasonal Beats ---")
            for beat in seasonal:
                parts.append(f"  {beat.get('month_range', '')}: {beat.get('note', '')}")

        trend = category.get("trend_signals", [])
        if trend:
            parts.append("--- Trend Signals ---")
            for t in trend[:3]:
                parts.append(f"  Query '{t.get('query', '')}': +{int(t.get('delta_yoy', 0)*100)}% YoY, age {t.get('segment_age', '')}, {t.get('skew', '')}")

        parts.append("\n=== MERCHANT CONTEXT ===")
        identity = merchant.get("identity", {})
        parts.append(f"Name: {identity.get('name', '')}")
        parts.append(f"Owner: {identity.get('owner_first_name', '')}")
        parts.append(f"Locality: {identity.get('locality', identity.get('city', ''))}")
        parts.append(f"Languages: {', '.join(identity.get('languages', []))}")

        perf = merchant.get("performance", {})
        parts.append(f"\nPerformance (30d window):")
        parts.append(f"  Views: {perf.get('views', 0)}, Calls: {perf.get('calls', 0)}, CTR: {perf.get('ctr', 0)}")
        parts.append(f"  Leads: {perf.get('leads', 0)}, Directions: {perf.get('directions', 0)}")
        delta = perf.get("delta_7d", {})
        if delta:
            parts.append(f"  7d delta: views {delta.get('views_pct', 0)*100:+.0f}%, calls {delta.get('calls_pct', 0)*100:+.0f}%, ctr {delta.get('ctr_pct', 0)*100:+.0f}%")

        offers = merchant.get("offers", [])
        active = [o for o in offers if o.get("status") == "active"]
        if active:
            parts.append(f"\nActive Offers:")
            for o in active:
                parts.append(f"  - {o.get('title', '')} (started {o.get('started', '')})")

        cust_agg = merchant.get("customer_aggregate", {})
        if cust_agg:
            parts.append(f"\nCustomer Aggregate:")
            parts.append(f"  Total unique YTD: {cust_agg.get('total_unique_ytd', 0)}")
            parts.append(f"  Lapsed 180d+: {cust_agg.get('lapsed_180d_plus', 0)}")
            parts.append(f"  6mo retention: {cust_agg.get('retention_6mo_pct', 0)*100:.0f}%")
            if cust_agg.get('high_risk_adult_count'):
                parts.append(f"  High-risk adult cohort: {cust_agg['high_risk_adult_count']}")

        signals = merchant.get("signals", [])
        if signals:
            parts.append(f"\nSignals: {', '.join(signals)}")

        reviews = merchant.get("review_themes", [])
        if reviews:
            parts.append(f"\nReview Themes:")
            for r in reviews[:3]:
                parts.append(f"  [{r.get('sentiment', '')}] {r.get('theme', '')}: {r.get('occurrences_30d', 0)}x - \"{r.get('common_quote', '')}\"")

        parts.append("\n=== TRIGGER CONTEXT ===")
        parts.append(f"Kind: {trigger.get('kind', '')}")
        parts.append(f"Urgency: {trigger.get('urgency', '')}")
        parts.append(f"Source: {trigger.get('source', '')}")
        payload = trigger.get("payload", {})
        if payload:
            parts.append(f"Payload: {json.dumps(payload)}")
        parts.append(f"Suppression key: {trigger.get('suppression_key', '')}")

        if customer:
            parts.append("\n=== CUSTOMER CONTEXT ===")
            cust_id = customer.get("identity", {})
            parts.append(f"Name: {cust_id.get('name', '')}")
            parts.append(f"Language preference: {cust_id.get('language_pref', customer.get('language_pref', ''))}")
            parts.append(f"State: {customer.get('state', '')}")
            if customer.get("relationship"):
                parts.append(f"Relationship: {customer['relationship']}")
            if customer.get("consent"):
                parts.append(f"Consent: {customer['consent']}")

        parts.append("\n=== RELEVANT FEW-SHOT EXAMPLES ===")
        trigger_kind = trigger.get("kind", "")
        matching_examples = self.few_shot_examples.get(trigger_kind, [])
        if matching_examples:
            for ex in matching_examples[:2]:
                parts.append(f"Example context: {ex.get('context', '')}")
                output = ex.get("output", {})
                parts.append(f"Example body: \"{output.get('body', '')}\"")
                parts.append(f"Example cta: {output.get('cta', '')}")
                parts.append("")
        else:
            parts.append("(No exact match for this trigger kind. Use the category voice and compulsion levers from system prompt.)")

        parts.append("\n=== YOUR TASK ===")
        parts.append("Compose a WhatsApp message using ALL relevant context above. Rules:")
        parts.append("1. Use real numbers, dates, and facts from the context - NEVER fabricate data")
        parts.append("2. Match the category voice (tone, register, code-mix) exactly")
        parts.append("3. Use the merchant's name/owner name correctly")
        parts.append("4. Connect the message to WHY NOW (the trigger)")
        parts.append("5. Include ONE clear CTA at the end")
        parts.append("6. Use 1+ compulsion levers: specificity, loss aversion, social proof, effort externalization, curiosity")
        parts.append("7. Keep it concise (WhatsApp-length, under 160 chars ideal)")
        parts.append("\nReturn ONLY valid JSON:")
        parts.append('{"body": "...", "cta": "binary_yes_no|open_ended|multi_choice_slot|none", "send_as": "vera|merchant_on_behalf", "suppression_key": "...", "rationale": "..."}')

        return "\n".join(parts)

    def _load_system_prompt(self) -> str:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, "src", "prompts", "system_prompt.txt")
            with open(path, "r") as f:
                return f.read()
        except:
            return "You are Vera, a merchant AI assistant. Compose WhatsApp messages using the 4-context framework."

    def _load_few_shot_examples(self) -> Dict[str, List[Dict[str, Any]]]:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, "src", "prompts", "few_shot_examples.json")
            with open(path, "r") as f:
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

    def _validate_specificity(self, body: str) -> bool:
        """Check if message has sufficient specificity (numbers, dates, sources)."""
        if not body:
            return False

        # Check for at least 2 numbers (counts, percentages, prices, dates)
        number_pattern = r'\d+[.,]?\d*[%₹]?|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4}'
        numbers_found = re.findall(number_pattern, body, re.IGNORECASE)
        if len(numbers_found) < 2:
            return False

        # Check for sources in clinical/pharmacy contexts
        if any(word in body.lower() for word in ['trial', 'study', 'journal', 'gazette', 'p.', 'vol.']):
            return True  # Source cited

        return len(numbers_found) >= 2
