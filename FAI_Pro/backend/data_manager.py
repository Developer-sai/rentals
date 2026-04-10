"""
data_manager.py
Lazily loads and normalizes CSV datasets for the Irish Housing Assistant.
"""
import os
import sys
import time
import pandas as pd
import numpy as np
from functools import lru_cache
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from logger import log_step, log_ok, log_warn

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))


@lru_cache(maxsize=1)
def load_rent_data() -> pd.DataFrame:
    """Load and normalize the full Irish rent dataset (RTB data)."""
    path = DATA_DIR / "irish_rent_full.csv"
    log_step("DATA", f"Loading CSV → {path.name}")
    t = time.time()
    df = pd.read_csv(path)
    df["county"] = df["county"].str.strip().str.title()
    df["area"] = df["area"].str.strip().str.title()
    df["rent_euro"] = pd.to_numeric(df["rent_euro"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    log_ok("DATA", f"Loaded {path.name}: {len(df):,} rows in {time.time()-t:.3f}s")
    return df


@lru_cache(maxsize=1)
def load_house_price_data() -> pd.DataFrame:
    """Load and normalize Dublin house prices dataset."""
    path = DATA_DIR / "dublin_house_prices_cleaned.csv"
    log_step("DATA", f"Loading CSV → {path.name}")
    t = time.time()
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["County"] = df["County"].str.strip().str.title()
    df["Date of Sale"] = pd.to_datetime(df["Date of Sale"], dayfirst=True, errors="coerce")
    df["Year"] = df["Date of Sale"].dt.year
    log_ok("DATA", f"Loaded {path.name}: {len(df):,} rows in {time.time()-t:.3f}s")
    return df


@lru_cache(maxsize=1)
def load_master_data() -> pd.DataFrame:
    """Load and normalize Master Dataset (macro county-level data)."""
    path = DATA_DIR / "Master_Dataset.csv"
    log_step("DATA", f"Loading CSV → {path.name}")
    t = time.time()
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df["County"] = df["County"].str.strip().str.title()
    df["Mean Sale Price"] = pd.to_numeric(df["Mean Sale Price"], errors="coerce")
    df["Median Annual Earnings"] = pd.to_numeric(df["Median Annual Earnings"], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    log_ok("DATA", f"Loaded {path.name}: {len(df):,} rows in {time.time()-t:.3f}s")
    return df


@lru_cache(maxsize=1)
def load_rent_by_county() -> pd.DataFrame:
    """Load county-level rent summary."""
    path = DATA_DIR / "irish_rent_by_county.csv"
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def get_counties() -> list[str]:
    df = load_rent_data()
    return sorted(df["county"].dropna().unique().tolist())


def get_years() -> list[int]:
    df = load_rent_data()
    return sorted(df["year"].dropna().astype(int).unique().tolist())


def get_rent_stats(county: str | None = None, year: int | None = None,
                   bedrooms: str | None = None) -> dict:
    """Compute rent statistics filtered by county/year/bedrooms."""
    df = load_rent_data()
    df = df[df["is_county_aggregate"] == True]

    if county:
        mask = df["county"].str.lower() == county.lower()
        df = df[mask]
    if year:
        df = df[df["year"] == year]
    if bedrooms and bedrooms != "all":
        df = df[df["bedrooms"].str.lower().str.contains(bedrooms.lower(), na=False)]

    if df.empty:
        return {"error": "No data found for the given filters."}

    return {
        "mean_rent": round(df["rent_euro"].mean(), 2),
        "median_rent": round(df["rent_euro"].median(), 2),
        "min_rent": round(df["rent_euro"].min(), 2),
        "max_rent": round(df["rent_euro"].max(), 2),
        "count": int(df.shape[0]),
        "counties": df["county"].unique().tolist() if not county else [county],
        "years": sorted(df["year"].dropna().astype(int).unique().tolist()),
    }


def compare_counties(county1: str, county2: str, year: int | None = None) -> dict:
    """Compare rent between two counties."""
    df = load_rent_data()
    df = df[df["is_county_aggregate"] == True]
    if year:
        df = df[df["year"] == year]

    def stats(c):
        sub = df[df["county"].str.lower() == c.lower()]
        if sub.empty:
            return None
        return {
            "mean_rent": round(sub["rent_euro"].mean(), 2),
            "latest_year": int(sub["year"].max()),
            "earliest_year": int(sub["year"].min()),
        }

    s1 = stats(county1)
    s2 = stats(county2)

    if not s1 or not s2:
        return {"error": f"Could not find data for one or both counties."}

    diff = round(s1["mean_rent"] - s2["mean_rent"], 2)
    pct = round((diff / s2["mean_rent"]) * 100, 1) if s2["mean_rent"] else 0

    return {
        county1: s1,
        county2: s2,
        "difference_euro": diff,
        "percentage_difference": pct,
        "more_expensive": county1 if diff > 0 else county2,
    }


def get_rent_trend(county: str, start_year: int = 2015, end_year: int = 2024) -> dict:
    """Compute year-over-year rent trend for a county."""
    df = load_rent_data()
    df = df[df["is_county_aggregate"] == True]
    df = df[df["county"].str.lower() == county.lower()]
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]

    if df.empty:
        return {"error": f"No trend data for {county}"}

    yearly = df.groupby("year")["rent_euro"].mean().reset_index()
    yearly = yearly.sort_values("year")

    trends = []
    for i, row in yearly.iterrows():
        entry = {"year": int(row["year"]), "avg_rent": round(row["rent_euro"], 2)}
        if i > 0:
            prev = yearly.iloc[list(yearly.index).index(i) - 1]["rent_euro"]
            change = round(((row["rent_euro"] - prev) / prev) * 100, 1)
            entry["yoy_change_pct"] = change
        trends.append(entry)

    total_change = 0
    if len(trends) >= 2:
        first = trends[0]["avg_rent"]
        last = trends[-1]["avg_rent"]
        total_change = round(((last - first) / first) * 100, 1)

    return {
        "county": county,
        "trend": trends,
        "total_change_pct": total_change,
        "start_year": start_year,
        "end_year": end_year,
    }


def get_house_price_stats(county: str | None = None, year: int | None = None) -> dict:
    """Get house price statistics."""
    df = load_house_price_data()
    if county:
        df = df[df["County"].str.lower() == county.lower()]
    if year:
        df = df[df["Year"] == year]

    if df.empty:
        return {"error": "No house price data found."}

    return {
        "mean_price": round(df["Price"].mean(), 2),
        "median_price": round(df["Price"].median(), 2),
        "min_price": round(df["Price"].min(), 2),
        "max_price": round(df["Price"].max(), 2),
        "count": int(df.shape[0]),
    }


def get_affordability(county: str, year: int | None = None) -> dict:
    """Calculate affordability: price-to-earnings ratio."""
    master = load_master_data()
    if county:
        master = master[master["County"].str.lower() == county.lower()]
    if year:
        master = master[master["Year"] == year]

    if master.empty:
        return {"error": f"No affordability data for {county}"}

    latest = master.sort_values("Year").iloc[-1]
    price = latest.get("Mean Sale Price")
    earnings = latest.get("Median Annual Earnings")

    ratio = round(price / earnings, 2) if earnings and earnings > 0 else None

    rent_stats = get_rent_stats(county=county, year=year)

    return {
        "county": county,
        "year": int(latest["Year"]),
        "mean_sale_price": round(price, 2) if price else None,
        "median_annual_earnings": round(earnings, 2) if earnings else None,
        "price_to_earnings_ratio": ratio,
        "avg_monthly_rent": rent_stats.get("mean_rent"),
        "rent_to_income_pct": round((rent_stats.get("mean_rent", 0) * 12) / earnings * 100, 1)
        if earnings else None,
    }
