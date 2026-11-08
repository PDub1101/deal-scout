"""
Generates 90-day realistic historical price envelopes for DealScout Flight Intelligence models:
- Corridors spanning holiday breaks, ski getaways, summer mountain hikes, and weekend shuttles
- Calibrated min, max, and median fare distributions
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
    # ATL <-> DEN MLK Long Weekend Ski (Jan 15, 2027 - Jan 19, 2027)
    "fl_atl_den_winter": {"min": 169, "max": 340, "avg": 235},
    # ATL <-> MCO Spring Break (Mar 12, 2027 - Mar 16, 2027)
    "fl_atl_mco_spring": {"min": 98, "max": 240, "avg": 158},
    # CLT <-> MIA South Beach Weekend Escape (Apr 9, 2027 - Apr 12, 2027)
    "fl_clt_mia_getaway": {"min": 135, "max": 290, "avg": 195},
}

def generate_history():
    history = {"flights": {}}

    for item_id, base in FLIGHT_BASELINES.items():
        series = []
        for _ in range(90):
            val = round(random.triangular(base["min"], base["max"], base["avg"]))
            series.append(val)
        history["flights"][item_id] = series

    target_file = DATA_DIR / "deal_history.json"
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"Successfully seeded 90-day flight historical time-series:")
    for item_id, series in history["flights"].items():
        print(f"  - {item_id}: {len(series)} points (range: ${min(series)} - ${max(series)})")

if __name__ == "__main__":
    generate_history()
