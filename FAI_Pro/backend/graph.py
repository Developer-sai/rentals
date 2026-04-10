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
from logger import log_start, log_step, log_ok, log_err, log_warn, log_sep, log_info, CYAN, GREEN, RED, YELLOW, RESET, BOLD

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
    salary: Optional[int]  # Annual salary in EUR if mentioned
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
    log_sep()
    log_start("PIPELINE", f"{BOLD}[STEP 1/5] INTENT AGENT starting{RESET}")
    log_step("INTENT", f"Query: '{state['query'][:100]}'")
    state["status"] = "Analyzing query..."

    try:
        intent = classify_intent(state["query"], state.get("history", []))
        state["intent"] = intent
        state["intent_type"] = intent.get("intent", "general_chat")
        state["county1"] = intent.get("county1")
        state["county2"] = intent.get("county2")
        state["year"] = intent.get("year")
        state["bedrooms"] = intent.get("bedrooms")
        state["salary"] = intent.get("salary")
        log_ok("INTENT", f"Done in {time.time()-start:.2f}s → intent={state['intent_type']} | county1={state['county1']} | salary={state['salary']}")
    except Exception as e:
        state["intent_type"] = "general_chat"
        state["error"] = str(e)
        log_err("INTENT", f"Failed: {e}")
    return state


def retrieval_node(state: HousingState) -> HousingState:
    """Retrieve data based on classified intent."""
    start = time.time()
    log_sep()
    log_start("PIPELINE", f"{BOLD}[STEP 2/5] RETRIEVAL AGENT starting{RESET}")
    log_step("RETRIEVAL", f"intent={state.get('intent_type')} | county={state.get('county1')} | year={state.get('year')} | bedrooms={state.get('bedrooms')}")
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
        sources = state.get('retrieval_source', [])
        log_ok("RETRIEVAL", f"Done in {time.time()-start:.2f}s → {len(state['data'])} field(s) retrieved | sources={sources}")
    except Exception as e:
        state["data"] = {}
        state["error"] = str(e)
        log_err("RETRIEVAL", f"Failed: {e}")
    return state


def web_search_node(state: HousingState) -> HousingState:
    """Wrapper for web search handler with logging."""
    start = time.time()
    log_sep()
    log_start("PIPELINE", f"{BOLD}[STEP 3/5] WEB SEARCH AGENT starting{RESET}")
    state["status"] = "Searching real-time web listings..."

    result = web_search_node_handler(state)

    web = state.get("web_results", {})
    if web and "results" in web:
        log_ok("WEB_SEARCH", f"Done in {time.time()-start:.2f}s → {len(web['results'])} live result(s) from Tavily")
    else:
        log_warn("WEB_SEARCH", f"Done in {time.time()-start:.2f}s → skipped (no real-time search needed)")
    return result


def analysis_node(state: HousingState) -> HousingState:
    """Run analysis on the retrieved data."""
    start = time.time()
    log_sep()
    log_start("PIPELINE", f"{BOLD}[STEP 4/5] ANALYSIS AGENT starting{RESET}")
    log_step("ANALYSIS", f"intent={state.get('intent_type')} | salary={state.get('salary')} | data_keys={list(state.get('data', {}).keys())[:6]}")
    state["status"] = "Calculating market metrics..."

    try:
        enriched = analyse(dict(state))
        state["analysis"] = enriched.get("analysis", {})
        log_ok("ANALYSIS", f"Done in {time.time()-start:.2f}s → {len(state['analysis'])} metric(s) computed: {list(state['analysis'].keys())}")
    except Exception as e:
        state["analysis"] = {}
        state["error"] = str(e)
        log_err("ANALYSIS", f"Failed: {e}")
    return state


def reasoning_node(state: HousingState) -> HousingState:
    """Use Groq LLM to reason and generate explanation."""
    start = time.time()
    log_sep()
    log_start("PIPELINE", f"{BOLD}[STEP 5a/5] REASONING AGENT (LLM) starting{RESET}")
    log_step("REASONING", f"Calling Groq LLM to synthesize answer...")
    state["status"] = "Synthesizing market advice..."

    try:
        enriched = reason(dict(state))
        state["reasoning"] = enriched.get("reasoning", "")
        log_ok("REASONING", f"Done in {time.time()-start:.2f}s → {len(state['reasoning'])} chars generated")
    except Exception as e:
        state["reasoning"] = "I encountered an error generating the response."
        state["error"] = str(e)
        log_err("REASONING", f"Failed: {e}")
    return state


def response_node(state: HousingState) -> HousingState:
    """Package the final response."""
    start = time.time()
    log_sep()
    log_start("PIPELINE", f"{BOLD}[STEP 5b/5] RESPONSE AGENT starting{RESET}")
    log_step("RESPONSE", "Packaging answer, chart data, sources, metrics...")
    state["status"] = "Preparing final response..."

    try:
        final = format_response(dict(state))
        state["answer"] = final.get("answer", "")
        state["chart_data"] = final.get("chart_data")
        state["sources"] = final.get("sources", [])
        state["key_metrics"] = final.get("key_metrics", {})
        log_ok("RESPONSE", f"Done in {time.time()-start:.2f}s → chart={state['chart_data'] is not None} | sources={len(state['sources'])} | metrics={len(state['key_metrics'])}")
        log_sep()
        log_ok("PIPELINE", f"{GREEN}{BOLD}ALL 5 STEPS COMPLETE ✓  answer={len(state['answer'])} chars{RESET}")
        log_sep()
    except Exception as e:
        state["answer"] = state.get("reasoning", "An error occurred.")
        state["error"] = str(e)
        log_err("RESPONSE", f"Failed: {e}")
    return state


# ──────────────────────────────────────────────
# Build Graph
# ──────────────────────────────────────────────
def build_graph():
    builder = StateGraph(HousingState)

    builder.add_node("intent_cls", intent_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("web_search", web_search_node)
    builder.add_node("analysis_proc", analysis_node)
    builder.add_node("reasoning_proc", reasoning_node)
    builder.add_node("response", response_node)

    builder.set_entry_point("intent_cls")
    builder.add_edge("intent_cls", "retrieval")
    builder.add_edge("retrieval", "web_search")
    builder.add_edge("web_search", "analysis_proc")
    builder.add_edge("analysis_proc", "reasoning_proc")
    builder.add_edge("reasoning_proc", "response")
    builder.add_edge("response", END)

    return builder.compile()


# Singleton graph
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
