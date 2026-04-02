"""
Analysis Agent
Performs calculations on the retrieved data: averages, trends, comparisons, ratios.
"""
import math


def analyse(retrieved: dict) -> dict:
    """Enrich retrieved data with computed metrics."""
    intent_type = retrieved.get("intent_type", "general_chat")
    data = retrieved.get("data", {})
    analysis = {}

    if intent_type == "rent_query":
        if "mean_rent" in data:
            analysis["annual_cost"] = round(data["mean_rent"] * 12, 2)
            analysis["weekly_cost"] = round(data["mean_rent"] / 4.33, 2)
            # Rough affordability threshold: 30% of income
            analysis["income_needed_30pct"] = round(data["mean_rent"] * 12 / 0.30, 2)
            analysis["summary"] = (
                f"Average monthly rent is €{data['mean_rent']:,.2f}, "
                f"which costs €{analysis['annual_cost']:,.2f} per year. "
                f"To keep rent under 30% of income, you'd need to earn at least "
                f"€{analysis['income_needed_30pct']:,.0f} per year."
            )

    elif intent_type == "house_price_query":
        if "mean_price" in data:
            analysis["annual_mortgage_estimate"] = round(data["mean_price"] * 0.065 / 12, 2)
            analysis["deposit_10pct"] = round(data["mean_price"] * 0.10, 2)
            analysis["deposit_20pct"] = round(data["mean_price"] * 0.20, 2)
            analysis["summary"] = (
                f"Mean house price is €{data['mean_price']:,.2f}. "
                f"A 10% deposit would be €{analysis['deposit_10pct']:,.0f}. "
                f"Estimated monthly mortgage (6.5% over 30yr) ≈ €{analysis['annual_mortgage_estimate']:,.0f}."
            )

    elif intent_type == "comparison":
        cmp = data.get("rent_comparison", {})
        if "difference_euro" in cmp:
            diff = cmp["difference_euro"]
            pct = cmp["percentage_difference"]
            more = cmp["more_expensive"]
            analysis["summary"] = (
                f"{more} is more expensive by €{abs(diff):,.2f}/month ({abs(pct):.1f}%). "
                f"Over a year, that's €{abs(diff)*12:,.0f} more."
            )
            analysis["annual_difference"] = round(abs(diff) * 12, 2)

    elif intent_type == "trend_analysis":
        trend = data.get("trend", [])
        total_change = data.get("total_change_pct", 0)
        if trend:
            latest = trend[-1]
            analysis["latest_avg_rent"] = latest.get("avg_rent")
            analysis["total_change_pct"] = total_change
            analysis["direction"] = "increasing" if total_change > 0 else "decreasing"
            years_covered = len(trend)
            avg_annual_change = round(total_change / years_covered, 1) if years_covered else 0
            analysis["avg_annual_change_pct"] = avg_annual_change
            analysis["summary"] = (
                f"Over the analysed period, rents in {data.get('county', '')} "
                f"have {'risen' if total_change > 0 else 'fallen'} by {abs(total_change):.1f}% "
                f"(avg {abs(avg_annual_change):.1f}%/year). "
                f"The most recent average is €{latest.get('avg_rent', 0):,.2f}/month."
            )

    elif intent_type == "affordability":
        ratio = data.get("price_to_earnings_ratio")
        rent_pct = data.get("rent_to_income_pct")
        if ratio:
            if ratio > 10:
                rating = "extremely unaffordable"
            elif ratio > 7:
                rating = "very unaffordable"
            elif ratio > 5:
                rating = "unaffordable"
            elif ratio > 3:
                rating = "moderately affordable"
            else:
                rating = "affordable"
            analysis["affordability_rating"] = rating
            analysis["summary"] = (
                f"Price-to-earnings ratio is {ratio}x ({rating}). "
                f"{'Rent consumes ' + str(rent_pct) + '% of median income.' if rent_pct else ''}"
            )

    retrieved["analysis"] = analysis
    return retrieved
