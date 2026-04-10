"""
Response Agent
Compiles the final user-facing response from reasoning output.
Adds structured metadata for the frontend to optionally display charts.
"""
import sys
import os
from urllib.parse import urlparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logger import log_step, log_ok, log_warn


def _clean_source_name(source: dict) -> str:
    """Extract a clean display name from a source dict using its URL."""
    url = source.get("url", "")
    if url:
        try:
            host = urlparse(url).netloc.lower()
            host = host.replace("www.", "")
            # Map known Irish property portals to canonical names
            _known = {
                "daft.ie": "Daft.ie",
                "myhome.ie": "MyHome.ie",
                "rent.ie": "Rent.ie",
                "property.ie": "Property.ie",
                "sherry fitzgerald": "Sherry FitzGerald",
                "greystar.com": "Greystar",
                "rtb.ie": "RTB",
                "cso.ie": "CSO",
                "gov.ie": "Gov.ie",
            }
            for key, label in _known.items():
                if key in host:
                    return label
            # Capitalize the domain without TLD as fallback
            return host.split(".")[0].capitalize()
        except Exception:
            pass
    title = source.get("title", "")
    return title[:30].split("–")[0].split("|")[0].strip().capitalize() or "Web Source"

def format_response(state: dict) -> dict:
    """Package the reasoning into a final response object with context-aware visualizations."""
    intent_type = state.get("intent_type", "general_chat")
    reasoning = state.get("reasoning", "I couldn't find relevant data for your query.")
    data = state.get("data", {})
    analysis = state.get("analysis", {})
    log_step("RESPONSE", f"intent={intent_type} | reasoning_len={len(reasoning)} | analysis_keys={list(analysis.keys())}")

    chart_data = None
    
    # SENIOR ENGINEER RULE: No random choices. Choose the best viz for the data.
    
    # 1. Trend Analysis -> Line Chart (Best for time-series)
    if intent_type == "trend_analysis" and "trend" in data:
        trend = data["trend"]
        chart_data = {
            "type": "line",
            "title": f"Rent Price Progression: {data.get('county', 'National')}",
            "labels": [str(t["year"]) for t in trend],
            "values": [t["avg_rent"] for t in trend],
            "unit": "€",
        }

    # 2. Comparison Queries -> Bar Chart (Best for side-by-side comparison)
    elif intent_type == "comparison":
        cmp = data.get("rent_comparison", {})
        counties = [k for k in cmp.keys() if isinstance(cmp[k], dict)]
        
        if len(counties) >= 2:
            chart_data = {
                "type": "bar",
                "title": f"Market Comparison: {counties[0]} vs {counties[1]}",
                "labels": counties,
                "values": [cmp[k]["mean_rent"] for k in counties],
                "unit": "€",
            }
        elif state.get("county1") and data.get("national_stats"):
            chart_data = {
                "type": "bar",
                "title": f"{state['county1']} vs National Average",
                "labels": [state['county1'], "National Average"],
                "values": [data.get("county_stats", {}).get("mean_rent", 0), data.get("national_stats", {}).get("mean_rent", 0)],
                "unit": "€",
            }

    # 3. Affordability/Rent Queries -> Doughnut (Best for parts-of-a-whole/ratios)
    elif intent_type in ("rent_query", "affordability"):
        monthly = data.get("mean_rent") or data.get("avg_monthly_rent") or analysis.get("latest_avg_rent")
        
        if monthly:
            # Show "30% Rule" visualization
            chart_data = {
                "type": "doughnut",
                "title": "Monthly Budget Allocation (30% Rule)",
                "labels": ["Rent", "Other Expenses"],
                "values": [monthly, (monthly / 0.30) - monthly],
                "unit": "€",
            }

    # 4. Fallback: If trend analysis is available as context, show it
    if not chart_data:
        trend_ctx = data.get("trend_context", {})
        if isinstance(trend_ctx, dict) and "trend" in trend_ctx:
            trend = trend_ctx["trend"]
            chart_data = {
                "type": "line",
                "title": f"Historical Context: {state.get('county1', 'Regional')}",
                "labels": [str(t["year"]) for t in trend],
                "values": [t["avg_rent"] for t in trend],
                "unit": "€",
            }

    # Professional clean-up of key_metrics
    cleaned_metrics = {}
    metric_map = {
        "latest_avg_rent": "Current Avg Rent",
        "yearly_change_pct": "Annual Growth",
        "affordability_index": "Affordability Score",
        "market_status": "Market Status",
        "difference_euro": "Rent Gap",
        "savings_potential": "Monthly Savings",
        "rent_to_income_pct": "Rent-to-Income %",
        "monthly_income": "Monthly Income",
        "monthly_disposable": "Monthly Disposable",
        "affordability_verdict": "Verdict",
        "annual_rent_cost": "Annual Rent Cost",
    }

    for k, v in analysis.items():
        if v is not None and v != "" and k != "summary":
            label = metric_map.get(k, k.replace("_", " ").title())
            cleaned_metrics[label] = v

    # OPTIMIZATION: Only show charts for high-value analytical intents
    analytical_intents = ("trend_analysis", "comparison", "affordability")
    if intent_type not in analytical_intents:
        chart_data = None
    if chart_data:
        log_step("RESPONSE", f"Chart generated: type={chart_data['type']} | labels={chart_data.get('labels',[])}")
    else:
        log_step("RESPONSE", "No chart (not an analytical intent)")

    # Show key metrics for affordability intent only
    if intent_type != "affordability":
        cleaned_metrics = {}

    # Sources: build clean deduplicated list of source names from URLs
    sources = state.get("sources", [])
    footer = ""
    if sources and reasoning:
        unique_names = list(dict.fromkeys(
            _clean_source_name(s) for s in sources if s.get("url") or s.get("title")
        ))[:4]
        if unique_names:
            footer = (
                "\n\n---\n**Sources**: "
                + " · ".join(unique_names)
                + " · RTB Historical Datasets"
            )
    log_ok("RESPONSE", f"Final answer: {len(reasoning + footer)} chars | metrics={len(cleaned_metrics)} | sources={len(sources)}")

    return {
        "answer": reasoning + footer,
        "intent": intent_type,
        "chart_data": chart_data,
        "sources": sources,
        "key_metrics": cleaned_metrics,
    }
