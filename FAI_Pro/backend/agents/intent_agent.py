"""
Intent Agent
Classifies the user's query into one of the structured intent types.
Uses Groq LLM for classification.
"""
import json
import os
import re
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

INTENT_SYSTEM_PROMPT = """You are an intent classifier for an Irish housing assistant.
Classify the user query into exactly ONE of these intents:
- rent_query: questions about rent prices, rental costs, rental market
- house_price_query: questions about buying/purchasing property prices
- comparison: comparing two locations, counties, or areas
- trend_analysis: trends over time, year-over-year, historical analysis
- affordability: rent-to-income, price-to-earnings, can I afford it
- recommendation: where should I live, best areas, suggestions
- meta_query: questions about the conversation history, summaries of what was discussed, or questions about the assistant's own functionality
- general_chat: greetings, or general questions not about housing and not about history

Return ONLY a JSON object with these fields:
{
  "intent": "<intent_type>",
  "county1": "<primary county or null>",
  "county2": "<secondary county for comparison or null>",
  "year": <year as integer or null>,
  "bedrooms": "<bedroom spec or null>",
  "confidence": <0.0-1.0>
}

Extract county names carefully. Irish counties: Dublin, Cork, Galway, Limerick, Waterford, 
Kilkenny, Wexford, Wicklow, Meath, Kildare, Louth, Westmeath, Offaly, Laois, Carlow, 
Longford, Cavan, Monaghan, Donegal, Sligo, Leitrim, Roscommon, Mayo, Clare, Tipperary, 
Kilkenny, Kerry.
"""


def classify_intent(query: str, history: list = []) -> dict:
    """Use Groq to classify the user's query intent and extract entities."""
    
    # Format history for the prompt
    history_str = ""
    # Use last 10 messages for better context recognition
    for msg in history[-10:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        # Truncate content for intent classification to keep it focused
        content = msg['content'][:150] + "..." if len(msg['content']) > 150 else msg['content']
        history_str += f"{role}: {content}\n"

    user_prompt = f"""Conversation History:
{history_str}

New User Query: {query}

Based on the history and the new query, identify the intent. If the user uses pronouns like 'it', 'there', or 'that', refer to the history to identify the location or topic."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()

    # Extract JSON from response
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Fallback intent
    return {
        "intent": "general_chat",
        "county1": None,
        "county2": None,
        "year": None,
        "bedrooms": None,
        "confidence": 0.3,
    }
