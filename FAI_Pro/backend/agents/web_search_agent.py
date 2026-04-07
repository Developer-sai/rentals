"""
Web Search Agent
Uses Tavily to fetch real-time market data, news, and listings.
"""
import os
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
        return {"error": "TAVILY_API_KEY not configured", "results": []}

    # Refine query for specific developments and prices
    search_query = f"{query} Ireland property rent prices"
    if "latest" in query.lower() or "recent" in query.lower():
        search_query = f"{query} site:daft.ie OR site:myhome.ie OR site:rent.ie"
    
    # If it's a specific apartment complex or location, focus the search
    # Example: "Griffith Wood" -> "Griffith Wood Dublin 9 rent prices"
    
    try:
        # Perform search
        # We use 'advanced' search for better quality in a premium tool
        response = tavily.search(
            query=search_query,
            search_depth="advanced",
            max_results=6,
            include_answer=True
        )
        
        return {
            "query": search_query,
            "results": response.get("results", []),
            "answer": response.get("answer", ""),
            "source": "Tavily Real-Time Search"
        }
    except Exception as e:
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
        # We let the graph node handler handle the logging to avoid circular imports
        state["status"] = "Searching real-time listings on Daft/MyHome..."
        web_results = search_web(query, intent_type)
        state["web_results"] = web_results
        
        # Add sources metadata
        if not state.get("sources"):
            state["sources"] = []
            
        # Perplexity style: Add specific site titles to sources
        for res in web_results.get("results", []):
            source_title = res.get("title", "Real-time Update")
            # If title is too long, truncate or clean
            if len(source_title) > 40:
                source_title = source_title[:37] + "..."
            state["sources"].append({
                "title": source_title,
                "url": res.get("url"),
                "site": "Web Site" # Can refine further if needed
            })
    else:
        state["web_results"] = {"context": "Skipped (Static data sufficient)"}
        
    return state
