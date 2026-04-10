"""
Reasoning Agent
Takes the analysis output and uses Groq LLM to produce a rich, contextual explanation.
"""
import json
import os
import time
from groq import Groq
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logger import log_step, log_llm, log_ok, log_err

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
    start = time.time()
    query = state.get("query", "")
    data = state.get("data", {})
    web_results = state.get("web_results", {})
    analysis = state.get("analysis", {})
    intent_type = state.get("intent_type", "general_chat")
    has_csv = bool(data and data != {"context": "general_conversation"})
    has_web = bool(web_results and web_results.get("results"))
    log_step("REASONING", f"Preparing context — csv_data={has_csv} | web_results={has_web} | analysis={bool(analysis)}")

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
        context_parts.append(f"Pre-Computed Analysis (USE THESE NUMBERS EXACTLY — do not invent ratios):\n{json.dumps(analysis, indent=2, default=str)}")

    context = "\n\n".join(context_parts) if context_parts else "No specific data retrieved."

    salary = state.get("salary")
    salary_note = f"\nUser's annual salary: €{salary:,}" if salary else ""

    # Format history for the prompt
    history = state.get("history", [])
    history_str = ""
    for msg in history[-10:]:
        role = "System" if msg["role"] == "bot" else "User"
        history_str += f"{role}: {msg['content'][:200]}...\n"

    user_message = f"""Conversation History:
{history_str}

New Question: {query}
Query Intent: {intent_type}{salary_note}

CONTEXTUAL DATA:
{context}

INSTRUCTIONS:
1. For specific apartment complexes or developments, prioritize Real-Time Web Data prices over CSV averages.
2. If salary data is provided in Pre-Computed Analysis, use those EXACT numbers (rent_to_income_pct, monthly_disposable, etc.) — do NOT recalculate or invent percentages.
3. If comparing 3 or more areas/years, use a Markdown table.
4. Keep it concise. Do not repeat context already in the conversation history.
5. Cite source names (Daft.ie, MyHome.ie, etc.) when they appear in the web data."""

    log_llm("REASONING", f"Calling Groq ({MODEL}) | max_tokens=1000 | temperature=0.3")
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
    usage = response.usage
    log_ok("REASONING", f"Generated {len(reasoning_text)} chars | tokens: prompt={usage.prompt_tokens} completion={usage.completion_tokens} total={usage.total_tokens} | {time.time()-start:.2f}s")
    state["reasoning"] = reasoning_text
    return state
