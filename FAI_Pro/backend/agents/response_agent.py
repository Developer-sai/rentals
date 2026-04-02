"""
Response Agent
Compiles the final user-facing response from reasoning output.
Adds structured metadata for the frontend to optionally display charts.
"""


import random

import random

def format_response(state: dict) -> dict:
    """Package the reasoning into a final response object with context-aware visualizations."""
    intent_type = state.get("intent_type", "general_chat")
    reasoning = state.get("reasoning", "I couldn't find relevant data for your query.")
    data = state.get("data", {})
    analysis = state.get("analysis", {})

    chart_data = None
    options = []

    # 1. Trend queries -> Line or Bar
    if intent_type == "trend_analysis" and "trend" in data:
        trend = data["trend"]
        ctype = random.choice(["line", "bar"])
        options.append({
            "type": ctype,
            "title": f"Rent Trend: {data.get('county', 'Ireland')}",
            "labels": [str(t["year"]) for t in trend],
            "values": [t["avg_rent"] for t in trend],
            "unit": "€",
        })

    # 2. Comparison -> Radar, Bar, or PolarArea
    elif intent_type == "comparison":
        cmp = data.get("rent_comparison", {})
        county_stats = data.get("county_stats")
        national_stats = data.get("national_stats")

        if "difference_euro" in cmp:
            keys = [k for k in cmp.keys() if k not in ("difference_euro", "percentage_difference", "more_expensive")]
            ctype = random.choice(["bar", "radar", "polarArea"])
            options.append({
                "type": ctype,
                "title": f"Comparison: {keys[0]} vs {keys[1]}" if len(keys)==2 else "Rent Comparison",
                "labels": keys,
                "values": [cmp[k]["mean_rent"] for k in keys if isinstance(cmp[k], dict)],
                "unit": "€",
            })
        elif county_stats and national_stats:
            ctype = random.choice(["bar", "polarArea"])
            options.append({
                "type": ctype,
                "title": f"{data.get('county', 'County')} vs National Average",
                "labels": [data.get("county", "County"), "National Average"],
                "values": [county_stats.get("mean_rent", 0), national_stats.get("mean_rent", 0)],
                "unit": "€",
            })

    # 3. Standard Rent / Affordability -> Doughnut, Bar, Line
    elif intent_type in ("rent_query", "affordability"):
        monthly = data.get("mean_rent") or data.get("avg_monthly_rent") or analysis.get("latest_avg_rent")
        
        if monthly:
            options.append({
                "type": "doughnut",
                "title": "Cost vs Recommended Income (30% Rule)",
                "labels": ["Rent", "Remaining Income (70%)"],
                "values": [monthly, monthly / 0.30 * 0.70],
                "unit": "€",
            })
            
        trend_context = data.get("trend_context")
        if trend_context and isinstance(trend_context, dict) and "trend" in trend_context:
            trend = trend_context["trend"]
            options.append({
                "type": "line",
                "title": f"Trailing 5-Year Growth: {data.get('county', 'County')}",
                "labels": [str(t["year"]) for t in trend],
                "values": [t["avg_rent"] for t in trend],
                "unit": "€",
            })
            options.append({
                "type": "radar",
                "title": f"Historical Rent Map: {data.get('county', 'County')}",
                "labels": [str(t["year"]) for t in trend],
                "values": [t["avg_rent"] for t in trend],
                "unit": "€",
            })

    # 4. Recommendation / Multi-County -> Bar or Radar
    elif intent_type == "recommendation" and "national_overview" in data:
        df = data["national_overview"]
        if isinstance(df, dict) and "counties" in df:
            # We don't have direct access to DataFrame here easily if serialized to dict,
            # but if we do, we could map it.
            pass

    if options:
        chart_data = random.choice(options)

    # Clean up key_metrics to look more dynamic and less hardcoded
    cleaned_metrics = {}
    for k, v in analysis.items():
        if v is not None and v != "" and k != "summary":
            # Rename keys dynamically to make them feel fresh
            new_key = k.replace("_pct", " %").replace("_", " ").title()
            # If it's a difference metric, maybe randomly prefix it
            if "difference" in k and random.choice([True, False]):
                new_key = "Net " + new_key
            if "cost" in k and random.choice([True, False]):
                new_key = "Est. " + new_key
            cleaned_metrics[new_key] = v

    return {
        "answer": reasoning,
        "intent": intent_type,
        "chart_data": chart_data,
        "sources": state.get("retrieval_source", []),
        "key_metrics": cleaned_metrics,
    }
