# DealScout — Autonomous Flight & Wishlist Price Intelligence Engine

Live Dashboard: [https://pdub1101.github.io/deal-scout/](https://pdub1101.github.io/deal-scout/)  
Master Portfolio Hub: [https://pdub1101.github.io/](https://pdub1101.github.io/)

DealScout is an automated personal price intelligence dashboard that tracks high-value flight routes and wishlist electronics/gear, cutting through artificial retail discounts using **rolling 90-day historical percentiles** and **Google Gemini qualitative gotcha auditing**.

---

## Key Features

1. **Watchlist Configuration (`config/watchlist.json`):**
   - Monitors target routes (e.g. `ATL -> JFK`, `ATL -> MIA`, `ATL -> HND`, `ATL -> LAX`) and wishlist gear (Sony WH-1000XM5, M3 MacBook Air, TaylorMade Qi10 Driver).
2. **Statistical Percentile Engine (`engine/percentile.py`):**
   - Calculates mathematical price percentiles against 90-day time-series envelopes, isolating true bottom 10–15% outliers.
3. **Gemini Qualitative Gotcha Audit (`engine/gemini_auditor.py`):**
   - Uses `gemini-3.5-flash-lite` to screen for restrictive Basic Economy baggage fees, red-eye departure times, excessive layovers, and seller authenticity before issuing a `BUY NOW` verdict.
4. **Zero-Hosting Serverless Dashboard (`frontend/index.html`):**
   - Clean slate-matte theme matching [Market Insight](https://pdub1101.github.io/market-insight/) and [Paul Gibson's Portfolio](https://pdub1101.github.io/).
   - Top metrics tracking: Active Watchlist items, Today's Hot Deals, and the cumulative **Total Dollars Saved Ledger**.
5. **Daily Autonomous GitHub Action (`.github/workflows/daily_scout.yml`):**
   - Runs every morning at 7:00 AM EST, scans for deals, and commits fresh data directly to GitHub Pages.

---

## Quickstart

```bash
# 1. Install dependencies
pip install google-genai python-dotenv requests

# 2. Seed 90-day historical baseline
python data/seed_history.py

# 3. Run the DealScout Intelligence Scan
python scout_deals.py

# 4. Open the Dashboard
open frontend/index.html
```
