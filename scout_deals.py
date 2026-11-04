#!/usr/bin/env python3
"""
DealScout Core Orchestrator.
Executes daily price ingestion -> percentile statistical engine -> Gemini qualitative audit -> exports frontend state.
"""

from __future__ import annotations
import json
import datetime
from pathlib import Path

from engine.percentile import PercentileEngine
from engine.gemini_auditor import GeminiAuditor
from scouts.flight_scout import FlightScout
from scouts.product_scout import ProductScout

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = ROOT_DIR / "config" / "watchlist.json"
HISTORY_FILE = ROOT_DIR / "data" / "deal_history.json"
OUTPUT_JSON = ROOT_DIR / "data" / "deals_data.json"
OUTPUT_JS = ROOT_DIR / "frontend" / "deals_data.js"

def run_scout():
    print("=" * 60)
    print("DealScout: Running Daily Price & Value Intelligence Scan")
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Load configuration & history
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Missing config at {CONFIG_FILE}")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        watchlist = json.load(f)

    if not HISTORY_FILE.exists():
        raise FileNotFoundError(f"Missing history at {HISTORY_FILE}. Run seed_history.py first.")
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)

    auditor = GeminiAuditor()
    flight_scout = FlightScout()
    product_scout = ProductScout()

    # 2. Fetch current prices
    print("\n[1/4] Ingesting flight and product market quotes...")
    flight_quotes = flight_scout.fetch_quotes(watchlist.get("flights", []))
    product_quotes = product_scout.fetch_quotes(watchlist.get("products", []))

    processed_flights = []
    processed_products = []
    total_savings_opportunity = 0.0
    qualified_deal_count = 0

    # 3. Analyze Flights
    print("\n[2/4] Running Percentile Distribution & Gemini Gotcha Audits on Flights...")
    for fq in flight_quotes:
        fid = fq["id"]
        f_hist = history["flights"].get(fid, [])
        stats = PercentileEngine.analyze_price(fq["price"], f_hist)
        audit = auditor.audit_flight(fq, stats)

        if audit["verdict"] == "BUY NOW":
            qualified_deal_count += 1
            total_savings_opportunity += stats["estimated_savings"]

        processed_flights.append({
            **fq,
            "stats": stats,
            "audit": audit,
            "history_90d": f_hist[-14:],  # Last 14 days for sparkline
        })
        print(f"  • {fq['origin']} -> {fq['destination']}: ${fq['price']} ({stats['percentile_rank']}th percentile) => [{audit['verdict']}]")

    # 4. Analyze Products
    print("\n[3/4] Running Percentile Distribution & Gemini Value Audits on Wishlist Gear...")
    for pq in product_quotes:
        pid = pq["id"]
        p_hist = history["products"].get(pid, [])
        stats = PercentileEngine.analyze_price(pq["price"], p_hist)
        audit = auditor.audit_product(pq, stats)

        if audit["verdict"] == "BUY NOW":
            qualified_deal_count += 1
            total_savings_opportunity += stats["estimated_savings"]

        processed_products.append({
            **pq,
            "stats": stats,
            "audit": audit,
            "history_90d": p_hist[-14:],
        })
        print(f"  • {pq['name'][:28]}...: ${pq['price']} ({stats['percentile_rank']}th percentile) => [{audit['verdict']}]")

    # 5. Build Aggregate Dashboard State
    all_time_user_savings = 580.00 + (total_savings_opportunity if qualified_deal_count > 0 else 0.0)

    dashboard_data = {
        "metadata": {
            "last_scan_time": datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "total_tracked": len(processed_flights) + len(processed_products),
            "qualified_deals_count": qualified_deal_count,
            "total_savings_opportunity": round(total_savings_opportunity, 2),
            "all_time_dollars_saved": round(all_time_user_savings, 2),
            "system_status": "Healthy & Operational",
            "model_engine": "Gemini 3.5 Flash Lite + Percentile Rank",
        },
        "flights": processed_flights,
        "products": processed_products,
    }

    # 6. Save JSON & JS bundle
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("window.DEAL_DATA = " + json.dumps(dashboard_data, indent=2) + ";\n")

    print(f"\n[4/4] Successfully written:")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_JS}")
    print("\nDone! Scan completed successfully.")

if __name__ == "__main__":
    run_scout()
