"""
Gemini Qualitative Flight Intelligence Auditor for DealScout.
Analyzes flight corridors, fare classes, baggage rules, connection risks, and seasonal demand.
Uses Google GenAI (gemini-2.5-flash / gemini-3.5-flash-lite) with resilient heuristic fallbacks.
"""

from __future__ import annotations
import os
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class GeminiAuditor:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model_name = "gemini-3.5-flash-lite"

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[GeminiAuditor] Warning: Failed to initialize Google GenAI client: {e}")

    def audit_flight(self, flight: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits a flight deal for hidden fees, baggage gotchas, schedule/connection risks, and holiday pricing.
        """
        origin = flight.get("origin")
        destination = flight.get("destination")
        origin_city = flight.get("origin_city", origin)
        dest_city = flight.get("destination_city", destination)
        airline = flight.get("airline", "Major Carrier")
        price = flight.get("price")
        stops = flight.get("stops", 0)
        layover_hrs = flight.get("layover_hrs", 0)
        connection = flight.get("connection")
        departure_time = flight.get("departure_time", "11:30 AM")
        arrival_time = flight.get("arrival_time", "2:30 PM")
        flight_duration = flight.get("flight_duration_hrs", "3h 30m")
        cabin = flight.get("cabin", "Main Cabin")
        window_name = flight.get("window_name", "Target Window")
        date_display = flight.get("date_display", "")
        duration_label = flight.get("duration_label", "")
        percentile = stats.get("percentile_rank", 50.0)
        savings = stats.get("estimated_savings", 0)
        median_price = stats.get("median_price", price)

        prompt = f"""
You are the DealScout Flight Intelligence auditor. Conduct a sharp travel audit for this flight corridor:
- Route: {origin} -> {destination} ({origin_city} to {dest_city})
- Travel Window: {window_name} ({date_display}, {duration_label})
- Airline & Fare: {airline} — {cabin}
- Quoted Price: ${price} roundtrip (Historical 90d Percentile: {percentile}th percentile, Estimated Savings vs Median: ${savings})
- Schedule: Depart {departure_time}, Arrive {arrival_time} (Total Travel Time: {flight_duration})
- Routing: {stops} stop(s){f' via {connection} ({layover_hrs}h layover)' if stops > 0 else ' (Nonstop Direct)'}

Analyze and determine:
1. Baggage & Cabin Traps: Note whether overhead carry-on is unbundled (e.g., Frontier/Spirit charge $45-$65, United Basic bans full carry-on, while Southwest includes 2 free checked bags, Delta/American Main Cabin include carry-on). Note if regional jets (CRJ-900/ERJ-175) require gate valet pink-tags.
2. Connection & Winter Hub Risks: If stops > 0, assess layover safety and weather exposure (especially winter connections in DEN, ORD, DFW, or CLT).
3. Holiday / Peak Demand Timing: Does this rate represent an actual bottom, or is it expected to drop?
4. Value Verdict: "BUY NOW" (if <= 20th percentile or high holiday demand value), "FAIR VALUE" (21st-45th percentile), or "WAIT / PASS" (>45th percentile).

Return ONLY valid JSON matching this schema:
{{
  "verdict": "BUY NOW" | "FAIR VALUE" | "WAIT / PASS",
  "baggage_status": "Short description of luggage rules (e.g. Free Overhead Roller Included, 2 Bags Free, or $45+ Carry-on Fee)",
  "gotchas": ["list of caveats like early departure, regional jet gate check, unbundled bag fees, or winter hub connection"],
  "positive_highlights": ["list of advantages like nonstop direct, complimentary bags, or top carrier reliability"],
  "rationale": "Crisp 2-sentence actionable booking recommendation for the traveler."
}}
"""
        if self.client:
            try:
                from google.genai import types
                config = types.GenerateContentConfig(response_mime_type="application/json")
                res = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                raw = res.text.strip()
                parsed = json.loads(raw)
                return parsed
            except Exception as e:
                print(f"[GeminiAuditor] LLM API note for {origin}->{destination}: {e}. Using expert heuristic engine.")

        # Expert heuristic fallback engine
        gotchas = []
        positives = []
        baggage_status = "Main Cabin: Standard carry-on & personal item included"

        # Nonstop vs layover checks
        if stops == 0:
            positives.append(f"Nonstop direct service ({flight_duration}) with zero layover disruption risk")
        else:
            if layover_hrs < 0.8:
                gotchas.append(f"Tight {layover_hrs}h layover connection in {connection} — high missed connection risk")
            elif layover_hrs > 2.5:
                gotchas.append(f"Extended layover: {layover_hrs} hours waiting in {connection}")
            else:
                positives.append(f"Manageable {layover_hrs}h connection in {connection}")

            if connection in ["DEN", "ORD", "JFK"] and any(m in date_display for m in ["Dec", "Jan", "Feb"]):
                gotchas.append(f"Winter hub caution: {connection} connections are subject to de-icing and snow delays")

        # Airline & Cabin checks
        if "Frontier" in airline or "Spirit" in airline:
            baggage_status = "Unbundled Fare: Overhead carry-on roller incurs $45–$65 fee each way"
            gotchas.append("Ultra-low-cost carrier: seat selection, overhead carry-on bags, and water cost extra")
        elif "Southwest" in airline:
            baggage_status = "Generous: 2 Free Checked Bags + Full Carry-on & Personal Item"
            positives.append("Southwest perk: 2 free checked bags included, saving up to $140 roundtrip")
        elif "Comfort+" in cabin or "First" in cabin:
            baggage_status = "Premium Fare: Free checked bag & complimentary premium drinks included"
            positives.append(f"Elevated cabin experience: extra legroom and priority boarding on {airline}")
        elif "Basic" in cabin:
            baggage_status = "Basic Economy: Seat assigned at gate, last boarding group"
            gotchas.append("Basic Economy restrictions: changes non-refundable and no complimentary advance seat selection")
        else:
            baggage_status = "Standard Main Cabin: Overhead roller carry-on & personal item included"
            positives.append(f"Full Main Cabin ticket on {airline} with standard seat choice & carry-on bag")

        # Regional Jet check
        if "Delta Connection" in airline or destination == "VLD" or "CRJ" in cabin:
            gotchas.append("Regional jet (CRJ-900): standard roller carry-ons require complimentary gate valet-check")

        # Early / late flight checks
        if "6:" in departure_time and "AM" in departure_time:
            gotchas.append(f"Early morning departure ({departure_time}) requires arriving at airport by 4:30 AM")

        # Holiday & peak season
        if "Holiday" in window_name or "Christmas" in window_name:
            positives.append("Peak holiday window: high demand period where seat inventory drops rapidly")

        # Verdict logic
        if percentile <= 20 or price <= flight.get("target_price", 999):
            verdict = "BUY NOW"
            rationale = f"Rare price bottom for {airline} during {window_name}, ranking in the lowest {percentile}% of historical fares ($${savings:.0f} below median). Secure this seat before fares surge."
        elif percentile <= 45:
            verdict = "FAIR VALUE"
            rationale = f"Competitive rate of ${price} for {airline} over {date_display}. A reasonable buy if travel dates are fixed."
        else:
            verdict = "WAIT / PASS"
            rationale = f"Fare sits near median historical levels (${median_price}). Recommend tracking this corridor for typical fare dips 4-6 weeks out."

        return {
            "verdict": verdict,
            "baggage_status": baggage_status,
            "gotchas": gotchas,
            "positive_highlights": positives,
            "rationale": rationale
        }
