# DealScout — Flight, Concert & Gear Price Intelligence Engine

Live Production Dashboard: [https://pdub1101.github.io/deal-scout/](https://pdub1101.github.io/deal-scout/)  
Master Portfolio Hub: [https://pdub1101.github.io/](https://pdub1101.github.io/)

DealScout is an automated personal price intelligence dashboard that tracks tailored flight corridors, live concert tickets, outdoor apparel, footwear, and premium tech/EDC gear. It cuts through deceptive sales tactics using **rolling 90-day historical percentile distributions** combined with **Google Gemini qualitative fee, sightline, and schedule auditing**.

---

## Tailored Intelligence Verticals

### 1. Flights with Explicit Travel Windows & Direct Google Flights Links
- **ATL ↔ SLC (Holiday Break):** Dec 20, 2026 – Jan 3, 2027 (14 Nights • Christmas/New Year peak ski window).
- **ATL ↔ SLC (Summer Mountain):** Jun 12, 2027 – Jun 20, 2027 (8 Nights • Wasatch summer hiking window).
- **ATL ↔ VLD (Holiday Semester Break):** Dec 22, 2026 – Jan 4, 2027 (13 Nights • Delta Connection SkyWest CRJ-900 Direct).
- **ATL ↔ CLT (Summer Weekend Shuttle):** Jul 9, 2027 – Jul 12, 2027 (3 Nights • Nonstop shuttle).
- **CLT ↔ SLC (Christmas Ski Week):** Dec 23, 2026 – Jan 2, 2027 (10 Nights • Transcontinental ski week).
- *Each flight card displays exact calendar dates, trip durations, and direct Google Flights search links.*

### 2. Live Music & Concert Tickets (SeatGeek / Ticketmaster)
- **The Stews (Atlanta):** The Eastern, Atlanta, GA (GA Floor & Mezzanine).
- **The Stews (Athens):** Georgia Theatre, Athens, GA (Balcony & GA Floor headline).
- **Penelope Road:** Terminal West / Aisle 5, Atlanta, GA (Southern Jam & Indie Rock club night).
- **Shaky Knees Music Festival:** Central Park, Atlanta, GA (3-Day GA pass resale floor tracker).
- **Gemini Junk Fee & Sightline Audit:** Audits secondary ticketing +25–30% service/facility junk fees and detects obstructed view seats (e.g. historic theater pillars or outdoor festival sound towers).

### 3. Apparel, Footwear & Boots
- **Patagonia Better Sweater 1/4-Zip Fleece:** Tracks end-of-season colorway clearance under $100 vs $159 MSRP across REI and Backcountry.
- **Carhartt Duck Canvas Active Jacket / WIP:** 12-oz firm-hand cotton duck canvas with 3M Thinsulate insulation.
- **Blundstone 500 / 550 Chelsea Boots:** Premium water-resistant leather with XRD shock-absorption technology.
- **Nike Basketball:** Nike G.T. Cut series (Cut 3 / Cut Cross) featuring full-length ZoomX foam cushioning.
- **Adidas Classics:** Adidas Samba OG and Gazelle low-tops with suede T-toe and gum rubber sole.

### 4. Tech & EDC
- **Sony WH-1000XM5:** Flagship wireless noise-canceling headphones (V1 + QN1 dual processors).
- **Peak Design Tech Pouch:** Weatherproof 200D recycled nylon protective travel organizer with origami pockets.

---

## System Architecture

1. **Watchlist Configuration (`config/watchlist.json`):**
   - Central JSON schema defining origin/destination, exact travel windows, artists, venues, retailer URLs, MSRP, and target budgets.
2. **Scout Layer (`scouts/`):**
   - `flight_scout.py`: Corridors with dates, durations, and deep Google Flights links.
   - `ticket_scout.py`: Primary and secondary ticket quote ingestion with all-in 25-30% junk fee calculations and sightline metadata.
   - `product_scout.py`: Curated clearance and retail quotes for apparel, footwear, and tech.
3. **Statistical Percentile Engine (`engine/percentile.py`):**
   - Computes empirical price percentiles against 90-day time-series envelopes, isolating true bottom 15–18% outliers.
4. **Gemini Qualitative Gotcha Auditor (`engine/gemini_auditor.py`):**
   - Leverages `gemini-3.5-flash-lite` with structured JSON output:
     - Baggage policies (Basic Economy unbundled fees vs Main Cabin, regional CRJ-900 valet gate-checks).
     - Ticket fee loads (+25-30% checkout damage) and structural obstruction flags.
     - Authorized retailer verification and clearance return policies.
5. **Responsive Dashboard UI (`index.html`):**
   - Refined Light Base & Soft Slate Dark Mode (supports standalone viewing and embedded iframe mode).
   - Category filtering: All Monitors, Flights, Concert Tickets, Apparel & Boots, Tech & EDC, Actionable Deals Only.
   - Interactive SVG sparklines and price percentile indicators.
6. **Autonomous Daily GitHub Actions Cron (`.github/workflows/daily_scout.yml`):**
   - Runs daily at 7:00 AM EST (12:00 UTC) to scan prices, run Gemini audits, and auto-deploy to GitHub Pages.

---

## Quickstart

```bash
# 1. Install dependencies
pip install google-genai python-dotenv requests

# 2. Seed 90-day historical envelopes
python data/seed_history.py

# 3. Execute DealScout Multi-Vertical Intelligence Scan
python scout_deals.py

# 4. Deploy to GitHub Pages
python deploy_dealscout.py
```
