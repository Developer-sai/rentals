"""
Reasoning Agent
Takes the analysis output and uses Groq LLM to produce a rich, contextual explanation.
"""
import json
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

REASONING_SYSTEM_PROMPT = """You are an expert Irish housing market analyst and advisor.
You have deep knowledge of:
- Ireland's housing crisis, RTB (Residential Tenancies Board) data
- Regional economic differences across Irish counties
- The impact of demand/supply imbalance, construction costs, and government policy
- Practical advice for renters, buyers, and investors in Ireland

CRITICAL RULE:
If the user's question is NOT about housing, property, real estate, rents, or mortgages (e.g., general knowledge, coding, weather, sports, politics), you MUST politely refuse to answer. Reply saying you are a dedicated property assistant and can only answer questions related to the housing and rental market. Do not attempt to answer off-topic queries under any circumstances.

Given structured data and analysis about the Irish housing market, provide:
1. A clear, insightful answer to the user's question
2. Context explaining WHY prices/trends are as they are
3. Practical advice or next steps

Be conversational, helpful, and specific. Use Irish context (e.g., mention Dublin commuter belt,
university towns, RPZ zones, Help-to-Buy scheme where relevant).
Keep responses under 300 words. Use bullet points where helpful.
Always ground your response in the actual data provided."""


def reason(state: dict) -> dict:
    """Use Groq LLM to reason about the data and generate a contextual response."""
    query = state.get("query", "")
    data = state.get("data", {})
    analysis = state.get("analysis", {})
    intent_type = state.get("intent_type", "general_chat")

    # Build context for LLM
    context_parts = []
    if data and data != {"context": "general_conversation"}:
        context_parts.append(f"Retrieved Data:\n{json.dumps(data, indent=2, default=str)}")
    if analysis:
        context_parts.append(f"Analysis Summary:\n{json.dumps(analysis, indent=2, default=str)}")

    context = "\n\n".join(context_parts) if context_parts else "No specific data retrieved."

    user_message = f"""User Question: {query}

Query Intent: {intent_type}

{context}

Please answer the user's question based on this data."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": REASONING_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
        max_tokens=600,
    )

    reasoning_text = response.choices[0].message.content.strip()
    state["reasoning"] = reasoning_text
    return state
