"""
Analysis Agent
Performs calculations on the retrieved data: averages, trends, comparisons, ratios.
"""
import sys
import os
import math
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logger import log_step, log_ok, log_err, log_warn


def _salary_metrics(monthly_rent: float, salary: int) -> dict:
    """Compute accurate salary-based affordability metrics."""
    monthly_income = salary / 12
    rent_to_income_pct = round((monthly_rent / monthly_income) * 100, 1)
    annual_rent = round(monthly_rent * 12, 2)
    disposable_monthly = round(monthly_income - monthly_rent, 2)

    if rent_to_income_pct <= 30:
        verdict = "affordable (within the 30% rule)"
    elif rent_to_income_pct <= 40:
        verdict = "stretched (30–40% of income — manageable but tight)"
    else:
        verdict = "unaffordable (above 40% of income — high financial stress)"

    return {
        "rent_to_income_pct": rent_to_income_pct,
        "monthly_income": round(monthly_income, 2),
        "monthly_disposable": disposable_monthly,
        "annual_rent_cost": annual_rent,
        "affordability_verdict": verdict,
    }


def analyse(retrieved: dict) -> dict:
    """Enrich retrieved data with computed metrics."""
    intent_type = retrieved.get("intent_type", "general_chat")
    data = retrieved.get("data", {})
    salary = retrieved.get("salary")
    analysis = {}
    start = time.time()

    if intent_type == "rent_query":
        if "mean_rent" in data:
            log_step("ANALYSIS", f"Computing rent metrics: mean_rent=€{data['mean_rent']:,.2f} | salary={salary}")
            analysis["annual_cost"] = round(data["mean_rent"] * 12, 2)
            analysis["weekly_cost"] = round(data["mean_rent"] / 4.33, 2)
            analysis["income_needed_30pct"] = round(data["mean_rent"] * 12 / 0.30, 2)
            analysis["summary"] = (
                f"Average monthly rent is €{data['mean_rent']:,.2f}, "
                f"which costs €{analysis['annual_cost']:,.2f} per year. "
                f"To keep rent under 30% of income, you'd need to earn at least "
                f"€{analysis['income_needed_30pct']:,.0f} per year."
            )
            if salary:
                analysis.update(_salary_metrics(data["mean_rent"], salary))

    elif intent_type == "house_price_query":
        if "mean_price" in data:
            log_step("ANALYSIS", f"Computing house price metrics: mean_price=€{data['mean_price']:,.2f} | salary={salary}")
            analysis["annual_mortgage_estimate"] = round(data["mean_price"] * 0.065 / 12, 2)
            analysis["deposit_10pct"] = round(data["mean_price"] * 0.10, 2)
            analysis["deposit_20pct"] = round(data["mean_price"] * 0.20, 2)
            analysis["summary"] = (
                f"Mean house price is €{data['mean_price']:,.2f}. "
                f"A 10% deposit would be €{analysis['deposit_10pct']:,.0f}. "
                f"Estimated monthly mortgage (6.5% over 30yr) ≈ €{analysis['annual_mortgage_estimate']:,.0f}."
            )
            if salary:
                mortgage_monthly = analysis["annual_mortgage_estimate"]
                analysis.update(_salary_metrics(mortgage_monthly, salary))

    elif intent_type == "affordability":
        ratio = data.get("price_to_earnings_ratio")
        rent_pct = data.get("rent_to_income_pct")
        monthly_rent = data.get("mean_rent") or data.get("avg_monthly_rent")
        log_step("ANALYSIS", f"Affordability check: ratio={ratio} | rent_pct={rent_pct} | monthly_rent={monthly_rent} | salary={salary}")
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
        # If user provided salary, compute personalised metrics
        if salary and monthly_rent:
            analysis.update(_salary_metrics(monthly_rent, salary))
        elif salary:
            analysis["monthly_income"] = round(salary / 12, 2)

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

    retrieved["analysis"] = analysis
    log_ok("ANALYSIS", f"Metrics computed in {time.time()-start:.3f}s: {list(analysis.keys())}")
    return retrieved
