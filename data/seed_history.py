"""
Generates 90-day realistic historical price envelopes for DealScout intelligence models:
- Tailored flights with explicit holiday/seasonal windows
- Live concert & music festival tickets (The Stews, Penelope Road, Shaky Knees)
- Curated apparel, footwear & boots (Patagonia, Carhartt, Blundstone, Nike, Adidas)
- Premium tech & EDC gear (Sony WH-1000XM5, Peak Design Tech Pouch)
"""

from __future__ import annotations
import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

FLIGHT_BASELINES = {
    # ATL <-> SLC Christmas / Holiday window (Dec 20, 2026 - Jan 3, 2027)
    "fl_atl_slc_holiday": {"min": 310, "max": 620, "avg": 445},
    # ATL <-> SLC Summer Mountain window (Jun 12, 2027 - Jun 20, 2027)
    "fl_atl_slc_summer": {"min": 218, "max": 440, "avg": 315},
    # ATL <-> VLD Holiday Semester Break (Dec 22, 2026 - Jan 4, 2027) Delta Connection
    "fl_atl_vld_holiday": {"min": 195, "max": 380, "avg": 275},
    # ATL <-> CLT Summer Weekend Shuttle (Jul 9, 2027 - Jul 12, 2027)
    "fl_atl_clt_weekend": {"min": 118, "max": 280, "avg": 178},
    # CLT <-> SLC Christmas Ski Week (Dec 23, 2026 - Jan 2, 2027)
    "fl_clt_slc_ski": {"min": 320, "max": 650, "avg": 465},
}

TICKET_BASELINES = {
    # The Stews at The Eastern (Atlanta)
    "tix_stews_eastern": {"min": 35.0, "max": 85.0, "avg": 55.0},
    # The Stews at Georgia Theatre (Athens)
    "tix_stews_georgia_theatre": {"min": 30.0, "max": 75.0, "avg": 48.0},
    # Penelope Road at Terminal West (Atlanta)
    "tix_penelope_road_atl": {"min": 25.0, "max": 52.0, "avg": 34.0},
    # Shaky Knees Music Festival 3-Day GA Pass (Central Park, Atlanta)
    "tix_shaky_knees_ga3day": {"min": 275.0, "max": 480.0, "avg": 365.0},
}

PRODUCT_BASELINES = {
    # Patagonia Better Sweater Fleece (Clearance under $100 vs $159 MSRP)
    "prod_patagonia_better_sweater": {"min": 89.0, "max": 159.0, "avg": 132.0},
    # Carhartt Duck Canvas Active Jacket / WIP
    "prod_carhartt_active_jacket": {"min": 95.0, "max": 139.99, "avg": 122.0},
    # Blundstone 500 / 550 Chelsea Boots
    "prod_blundstone_550": {"min": 159.0, "max": 229.95, "avg": 199.0},
    # Nike Basketball (GT Cut series)
    "prod_nike_gt_cut": {"min": 119.0, "max": 190.0, "avg": 158.0},
    # Adidas classics (Samba / Gazelle)
    "prod_adidas_samba_gazelle": {"min": 69.0, "max": 105.0, "avg": 89.0},
    # Sony WH-1000XM5 Noise-Canceling Headphones
    "prod_sony_xm5": {"min": 278.0, "max": 399.99, "avg": 348.0},
    # Peak Design Tech Pouch
    "prod_peak_design_tech_pouch": {"min": 44.0, "max": 64.95, "avg": 58.0},
}

def generate_history():
    history = {"flights": {}, "tickets": {}, "products": {}}

    for item_id, base in FLIGHT_BASELINES.items():
        series = []
        for _ in range(90):
            val = round(random.triangular(base["min"], base["max"], base["avg"]))
            series.append(val)
        history["flights"][item_id] = series

    for item_id, base in TICKET_BASELINES.items():
        series = []
        for _ in range(90):
            val = round(random.triangular(base["min"], base["max"], base["avg"]), 2)
            series.append(val)
        history["tickets"][item_id] = series

    for item_id, base in PRODUCT_BASELINES.items():
        series = []
        for _ in range(90):
            val = round(random.triangular(base["min"], base["max"], base["avg"]), 2)
            series.append(val)
        history["products"][item_id] = series

    target_file = DATA_DIR / "deal_history.json"
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"Successfully seeded 90-day historical time-series:")
    print(f"  - {len(FLIGHT_BASELINES)} flight corridors (with explicit travel windows)")
    print(f"  - {len(TICKET_BASELINES)} live concert & festival tickets")
    print(f"  - {len(PRODUCT_BASELINES)} apparel, footwear, and tech products")

if __name__ == "__main__":
    generate_history()
