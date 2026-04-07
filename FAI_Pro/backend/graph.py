"""
graph.py
LangGraph state machine defining the multi-agent pipeline.

Flow:
  START
    → intent_node       (classify intent + extract entities)
    → retrieval_node    (fetch relevant data from CSVs)
    → analysis_node     (compute metrics, summaries)
    → reasoning_node    (Groq LLM contextual explanation)
    → response_node     (format final output)
  END
"""
import os
import sys
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, END

from agents.intent_agent import classify_intent
from agents.retrieval_agent import retrieve_data
from agents.web_search_agent import web_search_node_handler
from agents.analysis_agent import analyse
from agents.reasoning_agent import reason
from agents.response_agent import format_response

# ──────────────────────────────────────────────
# Logging Utility
# ──────────────────────────────────────────────
def log_agent(agent_name: str, message: str, color: str = "\033[94m"):
    """Print a timed, colored log message to the console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    reset = "\033[0m"
    print(f"[{timestamp}] {color}[{agent_name}]{reset} {message}")

# ──────────────────────────────────────────────
class HousingState(TypedDict, total=False):
    query: str
    history: list # Conversational history
    intent: dict
    intent_type: str
    county1: Optional[str]
    county2: Optional[str]
    year: Optional[int]
    bedrooms: Optional[str]
    data: dict
    retrieval_source: list
    web_results: dict
    analysis: dict
    reasoning: str
    answer: str
    chart_data: Optional[dict]
    sources: list
    key_metrics: dict
    error: Optional[str]
    status: str  # For real-time UI updates

# ──────────────────────────────────────────────
# Node Functions
# ──────────────────────────────────────────────
def intent_node(state: HousingState) -> HousingState:
    """Classify the user query and extract entities."""
    start = time.time()
    log_agent("INTENT", f"Analyzing query: '{state['query']}'", "\033[96m")
    state["status"] = "Analyzing query..."
    
    try:
        # Pass history for context
        intent = classify_intent(state["query"], state.get("history", []))
        state["intent"] = intent
        state["intent_type"] = intent.get("intent", "general_chat")
        state["county1"] = intent.get("county1")
        state["county2"] = intent.get("county2")
        state["year"] = intent.get("year")
        state["bedrooms"] = intent.get("bedrooms")
        log_agent("INTENT", f"Classified as '{state['intent_type']}' in {time.time()-start:.2f}s", "\033[92m")
    except Exception as e:
        state["intent_type"] = "general_chat"
        state["error"] = str(e)
        log_agent("INTENT", f"Error: {e}", "\033[91m")
    return state


def retrieval_node(state: HousingState) -> HousingState:
    """Retrieve data based on classified intent."""
    start = time.time()
    log_agent("RETRIEVAL", f"Searching databases for {state.get('intent_type')}...", "\033[96m")
    state["status"] = "Consulting housing databases..."
    
    try:
        result = retrieve_data(
            intent={
                "intent": state.get("intent_type", "general_chat"),
                "county1": state.get("county1"),
                "county2": state.get("county2"),
                "year": state.get("year"),
                "bedrooms": state.get("bedrooms"),
            },
            query=state["query"],
        )
        state["data"] = result.get("data", {})
        state["retrieval_source"] = result.get("retrieval_source", [])
        log_agent("RETRIEVAL", f"Fetched {len(state['data'])} data points in {time.time()-start:.2f}s", "\033[92m")
    except Exception as e:
        state["data"] = {}
        state["error"] = str(e)
        log_agent("RETRIEVAL", f"Error: {e}", "\033[91m")
    return state


def web_search_node(state: HousingState) -> HousingState:
    """Wrapper for web search handler with logging."""
    start = time.time()
    log_agent("WEB_SEARCH", "Checking real-time web sources...", "\033[96m")
    state["status"] = "Searching real-time web listings..."
    
    result = web_search_node_handler(state)
    
    if state.get("web_results") and "results" in state["web_results"]:
        log_agent("WEB_SEARCH", f"Found {len(state['web_results']['results'])} live results in {time.time()-start:.2f}s", "\033[92m")
    else:
        log_agent("WEB_SEARCH", "Skipped or no results found.", "\033[93m")
    return result


def analysis_node(state: HousingState) -> HousingState:
    """Run analysis on the retrieved data."""
    start = time.time()
    log_agent("ANALYSIS", "Running statistical computations...", "\033[96m")
    state["status"] = "Calculating market metrics..."
    
    try:
        enriched = analyse(dict(state))
        state["analysis"] = enriched.get("analysis", {})
        log_agent("ANALYSIS", f"Completed computations in {time.time()-start:.2f}s", "\033[92m")
    except Exception as e:
        state["analysis"] = {}
        state["error"] = str(e)
        log_agent("ANALYSIS", f"Error: {e}", "\033[91m")
    return state


def reasoning_node(state: HousingState) -> HousingState:
    """Use Groq LLM to reason and generate explanation."""
    start = time.time()
    log_agent("REASONING", "Synthesizing insights with LLM...", "\033[96m")
    state["status"] = "Synthesizing market advice..."
    
    try:
        # Pass history for context
        enriched = reason(dict(state))
        state["reasoning"] = enriched.get("reasoning", "")
        log_agent("REASONING", f"Generated explanation in {time.time()-start:.2f}s", "\033[92m")
    except Exception as e:
        state["reasoning"] = "I encountered an error generating the response."
        state["error"] = str(e)
        log_agent("REASONING", f"Error: {e}", "\033[91m")
    return state


def response_node(state: HousingState) -> HousingState:
    """Package the final response."""
    start = time.time()
    log_agent("RESPONSE", "Formatting final output...", "\033[96m")
    state["status"] = "Preparing final response..."
    
    try:
        final = format_response(dict(state))
        state["answer"] = final.get("answer", "")
        state["chart_data"] = final.get("chart_data")
        state["sources"] = final.get("sources", [])
        state["key_metrics"] = final.get("key_metrics", {})
        log_agent("RESPONSE", f"Ready in {time.time()-start:.2f}s", "\033[92m")
    except Exception as e:
        state["answer"] = state.get("reasoning", "An error occurred.")
        state["error"] = str(e)
        log_agent("RESPONSE", f"Error: {e}", "\033[91m")
    return state


# ──────────────────────────────────────────────
# Build Graph
# ──────────────────────────────────────────────
def build_graph():
    builder = StateGraph(HousingState)

    builder.add_node("intent", intent_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("web_search", web_search_node)
    builder.add_node("analysis", analysis_node)
    builder.add_node("reasoning", reasoning_node)
    builder.add_node("response", response_node)

    builder.set_entry_point("intent")
    builder.add_edge("intent", "retrieval")
    builder.add_edge("retrieval", "web_search")
    builder.add_edge("web_search", "analysis")
    builder.add_edge("analysis", "reasoning")
    builder.add_edge("reasoning", "response")
    builder.add_edge("response", END)

    return builder.compile()


# Singleton graph
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
