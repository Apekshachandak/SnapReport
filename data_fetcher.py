"""
data_fetcher.py — RealEstateAPI.com market data fetcher for SnapReport.
Makes two API calls: market summary (0 credits) + recent sales (last 90 days).
"""

import os
import requests
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()
from cache_utils import load_market_data, save_market_data

REAPI_KEY = os.getenv("REAPI_KEY")
BASE_URL = "https://api.realestateapi.com/v2/PropertySearch"


def fetch_market_data(zip_code: str) -> dict:
    """
    Fetch live market data for a given ZIP code from RealEstateAPI.com.
    Returns a structured dict of market metrics.
    """
    if not REAPI_KEY:
        raise ValueError("REAPI_KEY not found in environment variables. Check your .env file.")

    # ---- Check ZIP-level cache (MVP filesystem cache) ----
    cached = load_market_data(zip_code)
    if cached:
        print(f"  [Cache] Serving cached market data for ZIP {zip_code}")
        return cached

    headers = {
        "x-api-key": REAPI_KEY,
        "Content-Type": "application/json",
    }

    # ---- Call 1: Market Summary (0 credits) ----
    print(f"  [API] Fetching market summary for ZIP {zip_code}...")
    summary_body = {
        "count": True,
        "summary": True,
        "zip": zip_code,
    }
    try:
        summary_resp = requests.post(BASE_URL, headers=headers, json=summary_body, timeout=30)
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Market summary API call failed — {e}")
        print(f"Response: {summary_resp.text[:500]}")
        raise SystemExit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error during market summary call — {e}")
        raise SystemExit(1)

    # Parse summary fields (handle nested structures from REAPI)
    summary = summary_data.get("summary", {})
    count_data = summary_data.get("count", {})

    median_price = (
        summary.get("medianListingPrice")
        or summary.get("medianPrice")
        or summary_data.get("medianListingPrice")
        or 0
    )
    days_on_market = (
        summary.get("medianDaysOnMarket")
        or summary.get("avgDaysOnMarket")
        or summary_data.get("medianDaysOnMarket")
        or 0
    )
    active_listings = (
        count_data.get("mlsActive")
        or summary.get("mlsActive")
        or summary_data.get("mlsActive")
        or 0
    )
    pending_listings = (
        count_data.get("mlsPending")
        or summary.get("mlsPending")
        or summary_data.get("mlsPending")
        or 0
    )
    high_equity = (
        count_data.get("highEquity")
        or summary.get("highEquity")
        or summary_data.get("highEquity")
        or 0
    )
    vacant = (
        count_data.get("vacant")
        or summary.get("vacant")
        or summary_data.get("vacant")
        or 0
    )
    owner_occupied = (
        count_data.get("ownerOccupied")
        or summary.get("ownerOccupied")
        or summary_data.get("ownerOccupied")
        or 0
    )

    # ---- Call 2: Recent Sales (last 90 days) ----
    print(f"  [API] Fetching recent sales for ZIP {zip_code}...")
    today = datetime.today()
    ninety_days_ago = today - timedelta(days=90)
    sales_body = {
        "size": 10,
        "zip": zip_code,
        "last_sale_date_min": ninety_days_ago.strftime("%Y-%m-%d"),
        "last_sale_date_max": today.strftime("%Y-%m-%d"),
    }
    try:
        sales_resp = requests.post(BASE_URL, headers=headers, json=sales_body, timeout=30)
        sales_resp.raise_for_status()
        sales_data = sales_resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Recent sales API call failed — {e}")
        print(f"Response: {sales_resp.text[:500]}")
        raise SystemExit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error during recent sales call — {e}")
        raise SystemExit(1)

    # Parse recent sales
    raw_sales = sales_data.get("data", [])
    recent_sales = []
    for prop in raw_sales:
        address = prop.get("address", {})
        if isinstance(address, dict):
            street = address.get("line1") or address.get("street") or ""
            city = address.get("city") or ""
            state = address.get("state") or ""
            full_address = f"{street}, {city}, {state}".strip(", ")
        else:
            full_address = str(address) if address else "N/A"

        sale_amount = (
            prop.get("lastSaleAmount")
            or prop.get("saleAmount")
            or prop.get("estimatedValue")
            or 0
        )
        sale_date = (
            prop.get("lastSaleDate")
            or prop.get("saleDate")
            or "N/A"
        )
        recent_sales.append({
            "address": full_address or "N/A",
            "saleAmount": int(sale_amount) if sale_amount else 0,
            "saleDate": sale_date,
        })

    report_date = today.strftime("%B %Y")

    result = {
        "zip": zip_code,
        "median_price": int(median_price) if median_price else 0,
        "days_on_market": round(float(days_on_market), 1) if days_on_market else 0.0,
        "active_listings": int(active_listings) if active_listings else 0,
        "pending_listings": int(pending_listings) if pending_listings else 0,
        "high_equity_count": int(high_equity) if high_equity else 0,
        "vacant_count": int(vacant) if vacant else 0,
        "owner_occupied": int(owner_occupied) if owner_occupied else 0,
        "recent_sales": recent_sales,
        "report_date": report_date,
    }

    # Save to cache (best-effort)
    try:
        save_market_data(zip_code, result)
    except Exception:
        pass
    return result
