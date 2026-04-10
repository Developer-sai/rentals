"""
Intent Agent
Classifies the user's query into one of the structured intent types.
Uses Groq LLM for classification.
"""
import json
import os
import re
import time
from groq import Groq
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logger import log_step, log_llm, log_ok, log_err, log_warn

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

INTENT_SYSTEM_PROMPT = """You are an intent classifier for an Irish housing assistant.
Classify the user query into exactly ONE of these intents:
- rent_query: questions about rent prices, rental costs, rental market
- house_price_query: questions about buying/purchasing property prices
- comparison: comparing two locations, counties, or areas
- trend_analysis: trends over time, year-over-year, historical analysis
- affordability: rent-to-income, price-to-earnings, can I afford it, salary mentioned alongside housing
- recommendation: where should I live, best areas, suggestions
- meta_query: questions about the conversation history or the assistant's own functionality
- general_chat: greetings, or general questions NOT about housing

CRITICAL RULES:
1. If the user mentions BOTH rent AND purchase/buy in the same query → use "affordability"
2. If the user mentions their salary, income, or earnings alongside a housing query → use "affordability"
3. If the query mentions a specific property name, apartment complex, or development → NEVER use "general_chat"; use "rent_query" or "house_price_query"
4. Queries like "what is the rent in X" or "how much to rent in X" → "rent_query"
5. Queries like "buy", "purchase", "price to buy" → "house_price_query"
6. Only use "general_chat" for true non-housing queries (e.g. "what is the weather")

Return ONLY a JSON object with these fields:
{
  "intent": "<intent_type>",
  "county1": "<primary county or null>",
  "county2": "<secondary county for comparison or null>",
  "year": <year as integer or null>,
  "bedrooms": "<bedroom spec e.g. '2 bedroom' or null>",
  "salary": <annual salary as integer if mentioned, else null>,
  "confidence": <0.0-1.0>
}

Extract county names carefully. Irish counties: Dublin, Cork, Galway, Limerick, Waterford,
Kilkenny, Wexford, Wicklow, Meath, Kildare, Louth, Westmeath, Offaly, Laois, Carlow,
Longford, Cavan, Monaghan, Donegal, Sligo, Leitrim, Roscommon, Mayo, Clare, Tipperary, Kerry.
"""

# Keywords that indicate a housing query even if LLM says general_chat
_HOUSING_KEYWORDS = [
    "rent", "rental", "buy", "purchase", "apartment", "flat", "house", "property",
    "bhk", "bedroom", "studio", "lease", "mortgage", "deposit", "afford",
    "salary", "income", "earnings", "price", "cost", "monthly", "weekly",
    "daft", "myhome", "rent.ie", "reit", "rpz",
]


def classify_intent(query: str, history: list = []) -> dict:
    """Use Groq to classify the user's query intent and extract entities."""
    start = time.time()
    log_step("INTENT", f"Classifying query: '{query[:80]}{'...' if len(query) > 80 else ''}'")
    log_step("INTENT", f"History context: {len(history)} message(s) available")

    # Format history for the prompt
    history_str = ""
    for msg in history[-10:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg['content'][:150] + "..." if len(msg['content']) > 150 else msg['content']
        history_str += f"{role}: {content}\n"

    user_prompt = f"""Conversation History:
{history_str}

New User Query: {query}

Based on the history and the new query, identify the intent. If the user uses pronouns like 'it', 'there', or 'that', refer to the history to identify the location or topic."""

    log_llm("INTENT", f"Calling Groq ({MODEL}) for intent classification...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=250,
    )

    raw = response.choices[0].message.content.strip()
    log_step("INTENT", f"Raw LLM response: {raw[:120]}")

    result = None
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            log_err("INTENT", f"JSON parse failed: {e}")

    if result is None:
        result = {
            "intent": "general_chat",
            "county1": None, "county2": None,
            "year": None, "bedrooms": None, "salary": None,
            "confidence": 0.3,
        }

    # ── Fallback guard: if LLM says general_chat but query has housing keywords,
    #    override to the most appropriate intent based on query content ──────────
    q_lower = query.lower()
    if result.get("intent") == "general_chat" and any(kw in q_lower for kw in _HOUSING_KEYWORDS):
        has_rent    = any(kw in q_lower for kw in ["rent", "rental", "lease", "bhk", "bedroom"])
        has_buy     = any(kw in q_lower for kw in ["buy", "purchase", "price", "mortgage"])
        has_salary  = any(kw in q_lower for kw in ["salary", "income", "earn", "€", "euro"])
        if has_salary or (has_rent and has_buy):
            result["intent"] = "affordability"
        elif has_buy:
            result["intent"] = "house_price_query"
        elif has_rent:
            result["intent"] = "rent_query"
        else:
            result["intent"] = "rent_query"
        result["confidence"] = max(result.get("confidence", 0.3), 0.65)
        log_warn("INTENT", f"general_chat overridden → '{result['intent']}' via keyword fallback")

    # ── If salary is in query but not extracted, parse it ────────────────────
    if not result.get("salary"):
        salary_match = re.search(r"(\d[\d,]*)\s*(?:euro|eur|€|k\b)", q_lower)
        if salary_match:
            raw_num = salary_match.group(1).replace(",", "")
            salary_val = int(raw_num)
            if "k" in q_lower[salary_match.end()-2:salary_match.end()+1]:
                salary_val *= 1000
            if 10000 <= salary_val <= 500000:
                result["salary"] = salary_val
                log_step("INTENT", f"Salary extracted via regex: €{salary_val:,}")

    log_ok("INTENT", (
        f"intent={result.get('intent')} | county1={result.get('county1')} | "
        f"county2={result.get('county2')} | year={result.get('year')} | "
        f"bedrooms={result.get('bedrooms')} | salary={result.get('salary')} | "
        f"confidence={result.get('confidence')} | {time.time()-start:.2f}s"
    ))
    return result
