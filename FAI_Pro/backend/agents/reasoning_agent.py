"""
Reasoning Agent
Takes the analysis output and uses Groq LLM to produce a rich, contextual explanation.
"""
import json
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

REASONING_SYSTEM_PROMPT = """You are a senior Irish housing market consultant. 
Your goal is to provide elite, data-driven advice with a premium, corporate tone similar to Perplexity or ChatGPT Pro.

STRATEGIC DIRECTIVES:
1. **Direct Answer**: Start immediately with the most critical finding. No conversational filler ("Hello", "Based on my data").
2. **Structural Excellence**: Use bold headers for every section:
   - #### Market Pulse (Context and current averages)
   - #### Data-Driven Insights (Deep analysis of the 'why')
   - #### Strategic Outlook (Predictions or professional recommendations)
3. **Elite Tone**: Be authoritative and analytical. Instead of "Prices are high," use "The persistent supply-demand imbalance continues to exert upward pressure on valuations."
4. **Contextual Memory**: Reference previous exchanges to build a cohesive narrative.
5. **Tables & Viz**: Always use Markdown tables for comparisons. Use bold text for key figures.

CRITICAL SCOPE:
- Primary expertise: Irish property, RTB trends, residential investments.
- Meta-queries: Summarize the conversation history professionally if asked.
- Out of Scope: Politley redirect non-housing queries with: "**Consultancy Scope**: My expertise is focused on the Irish residential and rental market. How can I assist you with property data?"
"""


def reason(state: dict) -> dict:
    """Use Groq LLM to reason about the data and generate a contextual response."""
    query = state.get("query", "")
    data = state.get("data", {})
    web_results = state.get("web_results", {})
    analysis = state.get("analysis", {})
    intent_type = state.get("intent_type", "general_chat")

    # Build context for LLM
    context_parts = []
    if data and data != {"context": "general_conversation"}:
        context_parts.append(f"Structured Data (CSV):\n{json.dumps(data, indent=2, default=str)}")
    
    if web_results and web_results.get("results"):
        search_summary = f"Real-Time Web Data (Tavily):\nAnswer Summary: {web_results.get('answer', 'N/A')}\n"
        search_summary += "Individual Search Results (PRIORITIZE THESE FOR SPECIFIC PROPERTIES):\n"
        for r in web_results["results"]:
            search_summary += f"- Title: {r.get('title')}\n  Snippet: {r.get('content')}\n  Source: {r.get('url')}\n"
        context_parts.append(search_summary)

    if analysis:
        context_parts.append(f"Broad Geographic Analysis (CSV-based):\n{json.dumps(analysis, indent=2, default=str)}")

    context = "\n\n".join(context_parts) if context_parts else "No specific data retrieved."

    # Format history for the prompt
    history = state.get("history", [])
    history_str = ""
    # Use last 10 messages for a broader context window
    for msg in history[-10:]:
        role = "System" if msg["role"] == "bot" else "User"
        history_str += f"{role}: {msg['content'][:200]}...\n"

    user_message = f"""Conversation History (Last 3):
{history_str}

New Question: {query}
Query Intent: {intent_type}

CONTEXTUAL DATA:
{context}

INSTRUCTIONS:
1. If the user is asking about a specific apartment complex or location (e.g., "Griffith Wood"), prioritize the 'Real-Time Web Data' prices above the 'Broad Geographic Analysis' averages.
2. If comparing 3 or more areas/years, use a professional Markdown table.
3. Keep it brief. Don't repeat previous greetings or context already discussed in the history.
4. Mention the specific sources (Daft, MyHome, etc.) by name if they appear in the web data."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": REASONING_SYSTEM_PROMPT + "\nALWAYS use Markdown tables for data comparisons. If data is limited, use concise bullet points."},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=1000,
    )

    reasoning_text = response.choices[0].message.content.strip()
    state["reasoning"] = reasoning_text
    return state
