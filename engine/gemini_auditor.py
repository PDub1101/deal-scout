"""
Gemini Qualitative "Gotcha & Value" Auditor.
Analyzes flights and product deals using Google GenAI (gemini-3.5-flash-lite)
to detect hidden fees, schedule traps, and artificial markdowns.
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
        Audits a flight deal for hidden fees, brutal schedules, and airline tier.
        """
        origin = flight.get("origin")
        destination = flight.get("destination")
        airline = flight.get("airline", "Major Carrier")
        price = flight.get("price")
        stops = flight.get("stops", 0)
        layover_hrs = flight.get("layover_hrs", 0)
        departure_time = flight.get("departure_time", "11:30 AM")
        cabin = flight.get("cabin", "Main Cabin")
        percentile = stats.get("percentile_rank", 50.0)
        savings = stats.get("estimated_savings", 0)

        prompt = f"""
You are the DealScout travel intelligence engine. Analyze this flight deal:
- Route: {origin} -> {destination}
- Airline: {airline}
- Ticket Price: ${price} roundtrip (Historical Percentile: {percentile}%, Estimated Savings: ${savings})
- Cabin Class: {cabin}
- Departure Time: {departure_time}
- Layovers: {stops} stop(s), total layover duration: {layover_hrs} hours

Evaluate whether this is a genuine high-value deal or a low-quality trap (e.g., restrictive Basic Economy carry-on fees, terrible 5 AM departures, long layovers, or budget airline unbundled fees).

Return ONLY valid JSON matching this schema:
{{
  "verdict": "BUY NOW" | "FAIR VALUE" | "WAIT / PASS",
  "gotchas": ["list of fine-print caveats, fees, or warnings, if any"],
  "positive_highlights": ["list of positive aspects like airline reputation, good time, luggage included"],
  "rationale": "Crisp 2-sentence summary explaining why the user should or should not book this fare."
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
                print(f"[GeminiAuditor] Fallback heuristic triggered for flight ({e})")

        # Heuristic fallback if LLM is unreachable
        gotchas = []
        positives = []
        if stops == 0:
            positives.append("Non-stop direct flight")
        elif layover_hrs > 3:
            gotchas.append(f"Extended {layover_hrs}h layover")

        if "Basic" in cabin:
            gotchas.append("Basic Economy ticket: Carry-on bag fees may apply ($35-$70 each way)")
        else:
            positives.append("Main Cabin fare: Standard carry-on and seat selection included")

        if percentile <= 15:
            verdict = "BUY NOW"
            rationale = f"Outstanding rate on {airline} landing in the lowest {percentile}% of historical fares. Strong buy recommendation."
        elif percentile <= 35:
            verdict = "FAIR VALUE"
            rationale = f"Solid price for {airline} with {stops} stops. Good option if travel dates are fixed."
        else:
            verdict = "WAIT / PASS"
            rationale = f"Fare sits near historical averages. High probability of price softening within the next 30 days."

        return {
            "verdict": verdict,
            "gotchas": gotchas,
            "positive_highlights": positives,
            "rationale": rationale
        }

    def audit_product(self, product: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits a consumer electronics / gear deal for authentic value and seller reliability.
        """
        name = product.get("name")
        retailer = product.get("retailer")
        current_price = product.get("price")
        msrp = product.get("retail_msrp")
        percentile = stats.get("percentile_rank", 50.0)
        savings = stats.get("estimated_savings", 0)

        prompt = f"""
You are the DealScout product intelligence engine. Analyze this retail deal:
- Product: {name}
- Retailer: {retailer}
- Current Deal Price: ${current_price} (MSRP: ${msrp})
- Historical Percentile: {percentile}%
- Calculated Savings vs Median: ${savings}

Evaluate whether this discount represents an authentic historical price drop vs a deceptive fake markdown or open-box risk.

Return ONLY valid JSON matching this schema:
{{
  "verdict": "BUY NOW" | "FAIR VALUE" | "WAIT / PASS",
  "gotchas": ["list of caveats like seller reputation, older model refresh risk, etc."],
  "positive_highlights": ["list of positive aspects like all-time low price, authorized dealer"],
  "rationale": "Crisp 2-sentence summary explaining whether to buy now or wait."
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
                print(f"[GeminiAuditor] Fallback heuristic triggered for product ({e})")

        # Heuristic fallback
        gotchas = []
        positives = [f"Sold by authorized vendor ({retailer})"]
        if percentile <= 15:
            verdict = "BUY NOW"
            rationale = f"All-time competitive pricing for {name}, saving approximately ${savings} against typical market rates."
        elif percentile <= 35:
            verdict = "FAIR VALUE"
            rationale = f"Decent promotional price for {name}, though occasional seasonal sales may discount another 5-10%."
        else:
            verdict = "WAIT / PASS"
            rationale = f"Current price is close to standard MSRP. Recommend waiting for a holiday promotional cycle."

        return {
            "verdict": verdict,
            "gotchas": gotchas,
            "positive_highlights": positives,
            "rationale": rationale
        }
