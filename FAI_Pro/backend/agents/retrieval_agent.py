"""
Retrieval Agent
Fetches relevant data from the datasets based on classified intent.
"""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logger import log_step, log_ok, log_err, log_warn

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
        log_step("RETRIEVAL", f"CSV lookup → get_rent_stats(county={county1}, year={year}, bedrooms={bedrooms})")
        start = time.time()
        data = get_rent_stats(county=county1, year=year, bedrooms=bedrooms)
        log_ok("RETRIEVAL", f"get_rent_stats returned {len(data)} field(s) in {time.time()-start:.3f}s")
        if county1:
            try:
                log_step("RETRIEVAL", f"Enriching → get_affordability(county={county1})")
                data["affordability_context"] = get_affordability(county=county1, year=year)
                log_step("RETRIEVAL", f"Enriching → get_rent_trend(county={county1}, 2020-2024)")
                data["trend_context"] = get_rent_trend(county=county1, start_year=2020, end_year=2024)
            except Exception as e:
                log_warn("RETRIEVAL", f"Enrichment skipped: {e}")
        result["data"] = data
        result["retrieval_source"] = ["irish_rent_full.csv", "Master_Dataset.csv"]

    elif intent_type == "house_price_query":
        log_step("RETRIEVAL", f"CSV lookup → get_house_price_stats(county={county1}, year={year})")
        start = time.time()
        data = get_house_price_stats(county=county1, year=year)
        log_ok("RETRIEVAL", f"get_house_price_stats returned {len(data)} field(s) in {time.time()-start:.3f}s")
        if county1:
            try:
                log_step("RETRIEVAL", f"Enriching → get_affordability(county={county1})")
                data["affordability_context"] = get_affordability(county=county1, year=year)
            except Exception as e:
                log_warn("RETRIEVAL", f"Affordability enrichment skipped: {e}")
        result["data"] = data
        result["retrieval_source"] = ["dublin_house_prices_cleaned.csv", "Master_Dataset.csv"]

    elif intent_type == "comparison":
        if county1 and county2:
            log_step("RETRIEVAL", f"CSV lookup → compare_counties({county1}, {county2}, year={year})")
            start = time.time()
            rent_cmp = compare_counties(county1, county2, year=year)
            log_ok("RETRIEVAL", f"compare_counties returned in {time.time()-start:.3f}s")
            result["data"] = {"rent_comparison": rent_cmp}
            result["retrieval_source"] = ["irish_rent_full.csv"]
        elif county1:
            log_step("RETRIEVAL", f"CSV lookup → {county1} vs national average (year={year})")
            county_stats = get_rent_stats(county=county1, year=year)
            national_stats = get_rent_stats(year=year)
            result["data"] = {"county_stats": county_stats, "national_stats": national_stats, "county": county1}
            result["retrieval_source"] = ["irish_rent_full.csv"]
        else:
            log_warn("RETRIEVAL", "Comparison requested but no counties identified")
            result["data"] = {"error": "Please specify two counties to compare."}

    elif intent_type == "trend_analysis":
        county = county1 or "Dublin"
        log_step("RETRIEVAL", f"CSV lookup → get_rent_trend(county={county}, 2015-2024)")
        start = time.time()
        trend = get_rent_trend(county, start_year=2015, end_year=2024)
        log_ok("RETRIEVAL", f"get_rent_trend returned {len(trend.get('trend',[]))} year(s) in {time.time()-start:.3f}s")
        result["data"] = trend
        result["retrieval_source"] = ["irish_rent_full.csv", "Master_Dataset.csv"]

    elif intent_type == "affordability":
        county = county1 or "Dublin"
        log_step("RETRIEVAL", f"CSV lookup → get_affordability(county={county}, year={year})")
        start = time.time()
        affords = get_affordability(county=county, year=year)
        log_ok("RETRIEVAL", f"get_affordability returned {len(affords)} field(s) in {time.time()-start:.3f}s")
        result["data"] = affords
        result["retrieval_source"] = ["Master_Dataset.csv", "irish_rent_full.csv"]

    elif intent_type == "recommendation":
        log_step("RETRIEVAL", f"CSV lookup → national rent overview (year={year or 2023})")
        start = time.time()
        rent_df = get_rent_stats(year=year or 2023)
        counties_list = get_counties()[:20]
        log_ok("RETRIEVAL", f"National overview ready in {time.time()-start:.3f}s | {len(counties_list)} counties loaded")
        result["data"] = {"national_overview": rent_df, "counties_available": counties_list}
        result["retrieval_source"] = ["irish_rent_full.csv", "Master_Dataset.csv"]

    else:
        log_warn("RETRIEVAL", f"intent='{intent_type}' → no CSV lookup needed (general chat)")
        result["data"] = {"context": "general_conversation"}
        result["retrieval_source"] = []

    return result
