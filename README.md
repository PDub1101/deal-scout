# DealScout — Flight Price Intelligence & Corridor Radar

Live Production Dashboard: [https://pdub1101.github.io/deal-scout/](https://pdub1101.github.io/deal-scout/)  
Master Portfolio Hub: [https://pdub1101.github.io/](https://pdub1101.github.io/)

DealScout is an automated personal flight price intelligence engine. It continuously tracks tailored travel corridors (holiday breaks, ski trips, weekend shuttles, seasonal vacations) using **rolling 90-day historical percentile distributions** combined with **Google Gemini qualitative fee, baggage, connection, and schedule audits**.

---

## Active Monitored Flight Corridors

Each corridor provides exact calendar dates, trip durations, carrier schedules, baggage status, and pre-populated direct booking links for **Google Flights** and **Kayak**:

1. **ATL ↔ SLC (Christmas / Holiday Ski Break):** Dec 20, 2026 – Jan 3, 2027 (14 Nights • Wasatch peak ski window).
2. **ATL ↔ SLC (Wasatch Summer Mountain Hiking):** Jun 12, 2027 – Jun 20, 2027 (8 Nights • Cottonwood Canyon hiking).
3. **ATL ↔ VLD (Holiday Semester Break):** Dec 22, 2026 – Jan 4, 2027 (13 Nights • Delta Connection SkyWest CRJ-900 Direct).
4. **ATL ↔ CLT (Summer Weekend Shuttle):** Jul 9, 2027 – Jul 12, 2027 (3 Nights • Nonstop Southeast shuttle).
5. **CLT ↔ SLC (Christmas Ski Week):** Dec 23, 2026 – Jan 2, 2027 (10 Nights • Transcon ski corridor).
6. **ATL ↔ DEN (MLK Long Weekend Ski):** Jan 15, 2027 – Jan 19, 2027 (4 Nights • Summit County ski getaway).
7. **ATL ↔ MCO (Spring Break Florida Getaway):** Mar 12, 2027 – Mar 16, 2027 (4 Nights • Nonstop Florida trip).
8. **CLT ↔ MIA (South Beach Spring Escape):** Apr 9, 2027 – Apr 12, 2027 (3 Nights • American Airlines hub-to-hub).

---

## Key Features

- **Empirical 90-Day Percentile Distributions:** Identifies true bottom 15–20% outliers vs historical median fares rather than misleading airline "sale" banners.
- **Gemini Qualitative Gotcha Auditor:** Audits each flight deal using Google GenAI:
  - *Baggage Rules:* Basic Economy carry-on bans (United) vs unbundled bag fees (Frontier/Spirit) vs 2 free checked bags (Southwest).
  - *Regional Jet Gotchas:* Pink valet gate-check tags on CRJ-900/ERJ-175 for standard roller bags.
  - *Connection & Winter Hub Risk:* Flags tight connections (< 50 mins) and winter de-icing delays in snow hubs (DEN, ORD, JFK).
  - *Holiday Supply Tightness:* Assesses seat inventory compression during Thanksgiving, Christmas, and Spring Break.
- **1-Click Deep Booking Links:** Directly launches pre-filled Google Flights and Kayak queries for exact travel dates and airport pairs.
- **Interactive Quick Flight Explorer:** Built-in dashboard drawer enabling search across any custom origin, destination, and travel dates.
- **Theme & Embedding Support:** Clean Light theme and Soft Slate Dark mode; seamlessly adapts inside iframes.

---

## How to Customize Your Flight Corridors

To track your own routes, edit `config/watchlist.json`:

```json
{
  "id": "fl_your_route_id",
  "origin": "ATL",
  "destination": "JFK",
  "origin_city": "Atlanta, GA",
  "destination_city": "New York, NY",
  "trip_type": "roundtrip",
  "window_name": "Fall Weekend Getaway",
  "category": "Weekend Shuttle",
  "start_date": "2027-10-15",
  "end_date": "2027-10-18",
  "date_display": "Oct 15, 2027 – Oct 18, 2027",
  "duration_nights": 3,
  "duration_label": "3 Nights (Weekend Trip)",
  "target_price": 140,
  "max_acceptable_price": 190,
  "preferred_airlines": ["Delta", "JetBlue"],
  "preferred_cabin": "Main Cabin",
  "max_layover_hrs": 0,
  "direct_preferred": true
}
```

---

## Quickstart

```bash
# 1. Install dependencies
pip install google-genai python-dotenv requests

# 2. Seed 90-day historical flight envelopes
python data/seed_history.py

# 3. Execute DealScout Flight Intelligence Scan
python scout_deals.py

# 4. Deploy to GitHub Pages
python deploy_dealscout.py
```
