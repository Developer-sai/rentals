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
sys.path.insert(0, os.path.dirname(__file__))

from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, END

from agents import (
    classify_intent,
    retrieve_data,
    analyse,
    reason,
    format_response,
)


# ──────────────────────────────────────────────
# State Schema
# ──────────────────────────────────────────────
class HousingState(TypedDict, total=False):
    query: str
    intent: dict
    intent_type: str
    county1: Optional[str]
    county2: Optional[str]
    year: Optional[int]
    bedrooms: Optional[str]
    data: dict
    retrieval_source: list
    analysis: dict
    reasoning: str
    answer: str
    chart_data: Optional[dict]
    sources: list
    key_metrics: dict
    error: Optional[str]


# ──────────────────────────────────────────────
# Node Functions
# ──────────────────────────────────────────────
def intent_node(state: HousingState) -> HousingState:
    """Classify the user query and extract entities."""
    try:
        intent = classify_intent(state["query"])
        state["intent"] = intent
        state["intent_type"] = intent.get("intent", "general_chat")
        state["county1"] = intent.get("county1")
        state["county2"] = intent.get("county2")
        state["year"] = intent.get("year")
        state["bedrooms"] = intent.get("bedrooms")
    except Exception as e:
        state["intent_type"] = "general_chat"
        state["error"] = str(e)
    return state


def retrieval_node(state: HousingState) -> HousingState:
    """Retrieve data based on classified intent."""
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
    except Exception as e:
        state["data"] = {}
        state["error"] = str(e)
    return state


def analysis_node(state: HousingState) -> HousingState:
    """Run analysis on the retrieved data."""
    try:
        enriched = analyse(dict(state))
        state["analysis"] = enriched.get("analysis", {})
    except Exception as e:
        state["analysis"] = {}
        state["error"] = str(e)
    return state


def reasoning_node(state: HousingState) -> HousingState:
    """Use Groq LLM to reason and generate explanation."""
    try:
        enriched = reason(dict(state))
        state["reasoning"] = enriched.get("reasoning", "")
    except Exception as e:
        state["reasoning"] = "I encountered an error generating the response."
        state["error"] = str(e)
    return state


def response_node(state: HousingState) -> HousingState:
    """Package the final response."""
    try:
        final = format_response(dict(state))
        state["answer"] = final.get("answer", "")
        state["chart_data"] = final.get("chart_data")
        state["sources"] = final.get("sources", [])
        state["key_metrics"] = final.get("key_metrics", {})
    except Exception as e:
        state["answer"] = state.get("reasoning", "An error occurred.")
        state["error"] = str(e)
    return state


# ──────────────────────────────────────────────
# Build Graph
# ──────────────────────────────────────────────
def build_graph():
    builder = StateGraph(HousingState)

    builder.add_node("intent", intent_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("analysis", analysis_node)
    builder.add_node("reasoning", reasoning_node)
    builder.add_node("response", response_node)

    builder.set_entry_point("intent")
    builder.add_edge("intent", "retrieval")
    builder.add_edge("retrieval", "analysis")
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
