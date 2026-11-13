#!/usr/bin/env python3
"""
DealScout Flight Intelligence Core Orchestrator.
Executes automated flight corridor price ingestion:
- Scans tailored flight corridors with explicit holiday and seasonal travel windows
- Fetches real-time market prices directly via Google Flights live data
- Computes empirical price percentiles against 90-day time-series envelopes
- Runs Google Gemini flight qualitative audits (baggage rules, connection risks, holiday supply tightness)
- Exports clean state bundles for the flight dashboard
"""

from __future__ import annotations
import json
import datetime
from pathlib import Path

from engine.percentile import PercentileEngine
from engine.gemini_auditor import GeminiAuditor
from scouts.flight_scout import FlightScout

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = ROOT_DIR / "config" / "watchlist.json"
HISTORY_FILE = ROOT_DIR / "data" / "deal_history.json"
OUTPUT_JSON = ROOT_DIR / "data" / "deals_data.json"
OUTPUT_JS_ROOT = ROOT_DIR / "deals_data.js"
OUTPUT_JS_FRONTEND = ROOT_DIR / "frontend" / "deals_data.js"

def run_scout():
    print("=" * 68)
    print("DealScout: Running Automated Flight Price Intelligence Scan")
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 68)

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

    # 2. Ingest flight quotes
    flight_watchlist = watchlist.get("flights", [])
    print(f"\n[1/3] Ingesting real-time market quotes for {len(flight_watchlist)} flight corridors...")
    flight_quotes = flight_scout.fetch_quotes(flight_watchlist)

    processed_flights = []
    total_savings_opportunity = 0.0
    qualified_deal_count = 0
    max_savings_amount = 0.0
    live_quotes_count = 0

    # 3. Analyze Flight Corridors
    print("\n[2/3] Computing 90-day Percentile Envelopes & Gemini Flight Audits...")
    flights_history = history.setdefault("flights", {})

    for fq in flight_quotes:
        fid = fq["id"]
        f_hist = flights_history.setdefault(fid, [])

        # Analyze price before appending so percentile is against existing envelope
        stats = PercentileEngine.analyze_price(fq["price"], f_hist)
        audit = auditor.audit_flight(fq, stats)

        # Append today's actual price to rolling 90-day history
        f_hist.append(fq["price"])
        if len(f_hist) > 90:
            f_hist.pop(0)

        if fq.get("is_live"):
            live_quotes_count += 1

        savings = stats.get("estimated_savings", 0.0)
        if audit["verdict"] == "BUY NOW":
            qualified_deal_count += 1
            total_savings_opportunity += savings
            if savings > max_savings_amount:
                max_savings_amount = savings

        processed_flights.append({
            **fq,
            "stats": stats,
            "audit": audit,
            "history_90d": f_hist[-14:],  # Last 14 days for sparklines
        })
        stops_str = "Nonstop" if fq["stops"] == 0 else f"{fq['stops']} stop ({fq['layover_hrs']}h in {fq.get('connection')})"
        live_tag = "[LIVE]" if fq.get("is_live") else "[BENCHMARK]"
        print(f"  {live_tag} {fq['origin']} -> {fq['destination']} ({fq['window_name']}): ${fq['price']} [{stops_str}]")
        print(f"     Percentile: {stats['percentile_rank']}th% | Median: ${stats['median_price']} | Verdict: [{audit['verdict']}]")

    # Persist updated history back to file
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    # 4. Aggregate Dashboard State
    total_flights = len(processed_flights)
    avg_price = round(sum(f["price"] for f in processed_flights) / max(1, total_flights), 1)

    dashboard_data = {
        "metadata": {
            "last_scan_time": datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "total_corridors": total_flights,
            "live_verified_count": live_quotes_count,
            "qualified_deals_count": qualified_deal_count,
            "total_savings_opportunity": round(total_savings_opportunity, 2),
            "max_single_savings": round(max_savings_amount, 2),
            "average_flight_price": avg_price,
            "system_status": "Operational & Live Market Connected",
            "model_engine": "Google Flights Real-Time Ingestion + Gemini Gotcha Auditor + 90-Day Percentile Radar",
        },
        "flights": processed_flights,
    }

    # 5. Write Data Files
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)

    js_content = "window.DEAL_DATA = " + json.dumps(dashboard_data, indent=2) + ";\n"

    with open(OUTPUT_JS_ROOT, "w", encoding="utf-8") as f:
        f.write(js_content)

    OUTPUT_JS_FRONTEND.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JS_FRONTEND, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"\n[3/3] Successfully exported state bundles:")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_JS_ROOT}")
    print(f"  - {OUTPUT_JS_FRONTEND}")
    print(f"  - {HISTORY_FILE} (Updated rolling price history)")
    print(f"\nExecution Summary:")
    print(f"  Tracked Corridors: {total_flights}")
    print(f"  Live Real-Time Quotes: {live_quotes_count}/{total_flights}")
    print(f"  Actionable BUY NOW Fares: {qualified_deal_count}")
    print(f"  Immediate Savings Pool: ${total_savings_opportunity:.2f}")
    print("\nFlight Intelligence Scan completed successfully.")

if __name__ == "__main__":
    run_scout()
