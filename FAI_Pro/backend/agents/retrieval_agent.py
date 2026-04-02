"""
Retrieval Agent
Fetches relevant data from the datasets based on classified intent.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_manager import (
    get_rent_stats,
    compare_counties,
    get_rent_trend,
    get_house_price_stats,
    get_affordability,
    get_counties,
    get_years,
)


def retrieve_data(intent: dict, query: str) -> dict:
    """Route the intent to the appropriate data retrieval function."""
    intent_type = intent.get("intent", "general_chat")
    county1 = intent.get("county1")
    county2 = intent.get("county2")
    year = intent.get("year")
    bedrooms = intent.get("bedrooms")

    result = {
        "intent_type": intent_type,
        "query": query,
        "data": {},
        "retrieval_source": [],
    }

    if intent_type == "rent_query":
        data = get_rent_stats(county=county1, year=year, bedrooms=bedrooms)
        # Enrich data with multi-dataset context for richer answers
        if county1:
            try:
                data["affordability_context"] = get_affordability(county=county1, year=year)
                data["trend_context"] = get_rent_trend(county=county1, start_year=2020, end_year=2024)
            except Exception:
                pass
        result["data"] = data
        result["retrieval_source"] = ["irish_rent_full.csv", "Master_Dataset.csv"]

    elif intent_type == "house_price_query":
        data = get_house_price_stats(county=county1, year=year)
        # Enrich with affordability
        if county1:
            try:
                data["affordability_context"] = get_affordability(county=county1, year=year)
            except Exception:
                pass
        result["data"] = data
        result["retrieval_source"] = ["dublin_house_prices_cleaned.csv", "Master_Dataset.csv"]

    elif intent_type == "comparison":
        if county1 and county2:
            rent_cmp = compare_counties(county1, county2, year=year)
            result["data"] = {"rent_comparison": rent_cmp}
            result["retrieval_source"] = ["irish_rent_full.csv"]
        elif county1:
            # Compare county vs national average
            county_stats = get_rent_stats(county=county1, year=year)
            national_stats = get_rent_stats(year=year)
            result["data"] = {
                "county_stats": county_stats,
                "national_stats": national_stats,
                "county": county1,
            }
            result["retrieval_source"] = ["irish_rent_full.csv"]
        else:
            # Extract two counties from query manually
            result["data"] = {"error": "Please specify two counties to compare."}

    elif intent_type == "trend_analysis":
        county = county1 or "Dublin"
        trend = get_rent_trend(county, start_year=2015, end_year=2024)
        result["data"] = trend
        result["retrieval_source"] = ["irish_rent_full.csv", "Master_Dataset.csv"]

    elif intent_type == "affordability":
        county = county1 or "Dublin"
        affords = get_affordability(county=county, year=year)
        result["data"] = affords
        result["retrieval_source"] = ["Master_Dataset.csv", "irish_rent_full.csv"]

    elif intent_type == "recommendation":
        # Fetch multi-county rent overview for recommendations
        rent_df = get_rent_stats(year=year or 2023)
        result["data"] = {
            "national_overview": rent_df,
            "counties_available": get_counties()[:20],
        }
        result["retrieval_source"] = ["irish_rent_full.csv", "Master_Dataset.csv"]

    else:
        # General chat — no data needed
        result["data"] = {"context": "general_conversation"}
        result["retrieval_source"] = []

    return result
