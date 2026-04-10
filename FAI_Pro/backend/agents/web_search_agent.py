"""
Web Search Agent
Uses Tavily to fetch real-time market data, news, and listings.
"""
import os
import time
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logger import log_step, log_llm, log_ok, log_err, log_warn
from tavily import TavilyClient

# Initialize Tavily Client
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def search_web(query: str, intent_type: str = "general_chat") -> dict:
    """
    Agentic Web Search: Refines the query and fetches real-time data.
    Focuses on Irish property portals (Daft, Rent.ie, Myhome).
    """
    if not TAVILY_API_KEY:
        log_err("WEB_SEARCH", "TAVILY_API_KEY is not set — skipping web search")
        return {"error": "TAVILY_API_KEY not configured", "results": []}

    q = query.strip()

    # Build intent-specific, targeted search queries
    if intent_type == "house_price_query":
        search_query = f"{q} property price buy Ireland site:daft.ie OR site:myhome.ie OR site:property.ie"
    elif intent_type == "affordability":
        search_query = f"{q} rent price buy Ireland daft.ie myhome.ie rent.ie"
    elif "latest" in q.lower() or "recent" in q.lower() or "current" in q.lower():
        search_query = f"{q} site:daft.ie OR site:myhome.ie OR site:rent.ie"
    else:
        search_query = f"{q} rent price Ireland daft.ie OR myhome.ie OR rent.ie"

    start = time.time()
    log_llm("WEB_SEARCH", f"Tavily search → '{search_query[:100]}'")

    try:
        response = tavily.search(
            query=search_query,
            search_depth="advanced",
            max_results=6,
            include_answer=True
        )
        results = response.get("results", [])
        log_ok("WEB_SEARCH", f"{len(results)} result(s) returned in {time.time()-start:.2f}s")
        for i, r in enumerate(results, 1):
            log_step("WEB_SEARCH", f"  [{i}] {r.get('title', 'N/A')[:60]} — {r.get('url', '')[:60]}")
        return {
            "query": search_query,
            "results": results,
            "answer": response.get("answer", ""),
            "source": "Tavily Real-Time Search"
        }
    except Exception as e:
        log_err("WEB_SEARCH", f"Tavily request failed: {e}")
        return {"error": str(e), "results": []}

def web_search_node_handler(state: dict) -> dict:
    """
    Handler for the LangGraph node.
    Decides if web search is necessary based on intent.
    """
    query = state.get("query", "").lower()
    intent_type = state.get("intent_type", "general_chat")
    
    # ADVANCED LOGIC: Search if:
    # 1. Any real-time keywords
    # 2. Specific property terms (2bhk, apartment, complex)
    # 3. Non-generic location (not just a county name)
    real_time_keywords = ["latest", "recent", "current", "now", "daft", "rent.ie", "myhome", "price", "cost"]
    property_keywords = ["2bhk", "1bhk", "3bhk", "apartment", "complex", "development", "wood", "square", "court", "park"]
    
    needs_web = (
        any(kw in query for kw in real_time_keywords) or 
        any(kw in query for kw in property_keywords) or
        intent_type in ("rent_query", "house_price_query", "recommendation")
    )
    
    # If it's just a general greeting or "hi", skip
    if intent_type == "general_chat" and not any(kw in query for kw in property_keywords):
        needs_web = False

    if needs_web:
        log_step("WEB_SEARCH", f"Web search triggered — intent='{intent_type}'")
        state["status"] = "Searching real-time listings on Daft/MyHome..."
        web_results = search_web(state.get("query", query), intent_type)
        state["web_results"] = web_results

        if not state.get("sources"):
            state["sources"] = []

        for res in web_results.get("results", []):
            source_title = res.get("title", "Real-time Update")
            if len(source_title) > 40:
                source_title = source_title[:37] + "..."
            state["sources"].append({
                "title": source_title,
                "url": res.get("url"),
                "site": "Web Site"
            })
    else:
        log_warn("WEB_SEARCH", f"Web search skipped — intent='{intent_type}' does not require real-time data")
        state["web_results"] = {"context": "Skipped (Static data sufficient)"}

    return state
