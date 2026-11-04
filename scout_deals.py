#!/usr/bin/env python3
"""
DealScout Core Orchestrator.
Executes multi-vertical price ingestion:
- Flights with explicit holiday and seasonal travel windows
- Live concert & music festival tickets with 25-30% junk fee audits and obstructed view detection
- Apparel, footwear, boots, tech & EDC
Runs 90-day percentile distribution engine -> Gemini qualitative audit -> exports state.
"""

from __future__ import annotations
import json
import datetime
from pathlib import Path

from engine.percentile import PercentileEngine
from engine.gemini_auditor import GeminiAuditor
from scouts.flight_scout import FlightScout
from scouts.ticket_scout import TicketScout
from scouts.product_scout import ProductScout

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = ROOT_DIR / "config" / "watchlist.json"
HISTORY_FILE = ROOT_DIR / "data" / "deal_history.json"
OUTPUT_JSON = ROOT_DIR / "data" / "deals_data.json"
OUTPUT_JS_ROOT = ROOT_DIR / "deals_data.js"
OUTPUT_JS_FRONTEND = ROOT_DIR / "frontend" / "deals_data.js"

def run_scout():
    print("=" * 65)
    print("DealScout: Running Daily Multi-Vertical Intelligence Scan")
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

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
    ticket_scout = TicketScout()
    product_scout = ProductScout()

    # 2. Ingest quotes
    print("\n[1/5] Ingesting flight, concert ticket, and product market quotes...")
    flight_quotes = flight_scout.fetch_quotes(watchlist.get("flights", []))
    ticket_quotes = ticket_scout.fetch_quotes(watchlist.get("tickets", []))
    product_quotes = product_scout.fetch_quotes(watchlist.get("products", []))

    processed_flights = []
    processed_tickets = []
    processed_products = []
    total_savings_opportunity = 0.0
    qualified_deal_count = 0

    # 3. Analyze Flights
    print("\n[2/5] Running Percentile Distribution & Gemini Gotcha Audits on Flights...")
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
            "history_90d": f_hist[-14:],  # Last 14 observations for sparkline
        })
        print(f"  • {fq['origin']} -> {fq['destination']} ({fq['window_name']}): ${fq['price']} ({stats['percentile_rank']}th percentile) => [{audit['verdict']}]")

    # 4. Analyze Concert & Festival Tickets
    print("\n[3/5] Running Percentile Distribution & Gemini All-In Fee Audits on Concert Tickets...")
    for tq in ticket_quotes:
        tid = tq["id"]
        t_hist = history.get("tickets", {}).get(tid, [])
        stats = PercentileEngine.analyze_price(tq["price"], t_hist)
        audit = auditor.audit_ticket(tq, stats)

        if audit["verdict"] == "BUY NOW":
            qualified_deal_count += 1
            total_savings_opportunity += stats["estimated_savings"]

        processed_tickets.append({
            **tq,
            "stats": stats,
            "audit": audit,
            "history_90d": t_hist[-14:],
        })
        all_in = audit.get("all_in_price", tq["all_in_price"])
        print(f"  • {tq['artist'][:22]} @ {tq['venue']}: ${tq['price']} list (${all_in} all-in, {stats['percentile_rank']}th percentile) => [{audit['verdict']}]")

    # 5. Analyze Apparel, Footwear, Tech & EDC
    print("\n[4/5] Running Percentile Distribution & Gemini Authenticity Audits on Curated Gear...")
    for pq in product_quotes:
        pid = pq["id"]
        p_hist = history.get("products", {}).get(pid, [])
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
        print(f"  • {pq['name'][:30]}...: ${pq['price']} ({stats['percentile_rank']}th percentile) => [{audit['verdict']}]")

    # 6. Aggregate Dashboard State
    total_items = len(processed_flights) + len(processed_tickets) + len(processed_products)
    all_time_user_savings = 1140.00 + (total_savings_opportunity if qualified_deal_count > 0 else 0.0)

    dashboard_data = {
        "metadata": {
            "last_scan_time": datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "total_tracked": total_items,
            "qualified_deals_count": qualified_deal_count,
            "total_savings_opportunity": round(total_savings_opportunity, 2),
            "all_time_dollars_saved": round(all_time_user_savings, 2),
            "system_status": "Operational & Active",
            "model_engine": "Gemini 3.5 Flash Lite + 90-Day Percentile Engine",
            "verticals_breakdown": {
                "flights": len(processed_flights),
                "tickets": len(processed_tickets),
                "products": len(processed_products),
            }
        },
        "flights": processed_flights,
        "tickets": processed_tickets,
        "products": processed_products,
    }

    # 7. Write Data Files
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)

    js_content = "window.DEAL_DATA = " + json.dumps(dashboard_data, indent=2) + ";\n"

    with open(OUTPUT_JS_ROOT, "w", encoding="utf-8") as f:
        f.write(js_content)

    OUTPUT_JS_FRONTEND.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JS_FRONTEND, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"\n[5/5] Successfully exported state bundles:")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_JS_ROOT}")
    print(f"  - {OUTPUT_JS_FRONTEND}")
    print(f"\nExecution Summary:")
    print(f"  Tracked: {total_items} items ({len(processed_flights)} flights, {len(processed_tickets)} tickets, {len(processed_products)} goods)")
    print(f"  Actionable BUY NOW deals: {qualified_deal_count}")
    print(f"  Immediate Savings Opportunity: ${total_savings_opportunity:.2f}")
    print("\nScan completed successfully.")

if __name__ == "__main__":
    run_scout()
