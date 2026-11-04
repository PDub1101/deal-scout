"""
Gemini Qualitative "Gotcha & Value" Auditor for DealScout.
Analyzes flights, concert/event tickets, and curated gear using Google GenAI (gemini-3.5-flash-lite).
Audits:
- Hidden travel fees, baggage traps, and holiday scheduling surcharges
- Concert all-in junk fees (25-30% service fees) and obstructed view seats
- Artificial retail markdowns, authorized dealer validity, and clearance authenticity
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
        Audits a flight deal for hidden fees, baggage gotchas, schedule traps, and holiday pricing.
        """
        origin = flight.get("origin")
        destination = flight.get("destination")
        airline = flight.get("airline", "Major Carrier")
        price = flight.get("price")
        stops = flight.get("stops", 0)
        layover_hrs = flight.get("layover_hrs", 0)
        departure_time = flight.get("departure_time", "11:30 AM")
        cabin = flight.get("cabin", "Main Cabin")
        window_name = flight.get("window_name", "Target Window")
        date_display = flight.get("date_display", "")
        duration_label = flight.get("duration_label", "")
        percentile = stats.get("percentile_rank", 50.0)
        savings = stats.get("estimated_savings", 0)

        prompt = f"""
You are the DealScout travel intelligence engine. Audit this flight deal:
- Route: {origin} -> {destination} ({flight.get('origin_city')} to {flight.get('destination_city')})
- Travel Window: {window_name} ({date_display}, {duration_label})
- Airline / Operator: {airline}
- Ticket Price: ${price} roundtrip (Historical 90d Percentile: {percentile}%, Estimated Savings vs Median: ${savings})
- Cabin Class: {cabin}
- Departure Time: {departure_time}
- Layovers: {stops} stop(s), total layover duration: {layover_hrs} hours

Evaluate whether this is a genuine high-value fare or a deceptive trap:
1. Examine baggage rules (e.g. Basic Economy unbundled carry-on fees vs Main Cabin standard overhead roller).
2. For regional jets (e.g. Delta Connection CRJ-900 to Valdosta VLD), note regional gate-check (pink tag) norms for standard roller bags.
3. For peak travel windows (Christmas/Holiday Dec 20 - Jan 3 or Summer Mountain June), assess holiday supply tightness.

Return ONLY valid JSON matching this schema:
{{
  "verdict": "BUY NOW" | "FAIR VALUE" | "WAIT / PASS",
  "gotchas": ["list of caveats like luggage fees, early departure times, or connection risks"],
  "positive_highlights": ["list of positive aspects like direct routing, holiday availability, reputable carrier"],
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
                print(f"[GeminiAuditor] Heuristic fallback for flight {origin}->{destination} ({e})")

        # Heuristic fallback if LLM is unreachable
        gotchas = []
        positives = []
        if stops == 0:
            positives.append("Non-stop direct routing with zero connection risk")
        elif layover_hrs > 2.5:
            gotchas.append(f"Extended {layover_hrs}h layover connection")

        if "Basic" in cabin:
            gotchas.append("Basic Economy fare: overhead carry-on bag restricted or incur $35–$65 unbundled fees")
        else:
            positives.append("Main Cabin standard fare: overhead carry-on roller & personal item included")

        if "Delta Connection" in airline or destination == "VLD":
            gotchas.append("Regional jet (CRJ-900): standard roller carry-ons require complimentary gate valet-check")

        if percentile <= 18:
            verdict = "BUY NOW"
            rationale = f"Rare price bottom for {airline} during {window_name}, ranking in the lowest {percentile}% of historical fares. Book before seats fill."
        elif percentile <= 40:
            verdict = "FAIR VALUE"
            rationale = f"Competitive rate for {airline} over {date_display}. A reliable option if holiday dates are firm."
        else:
            verdict = "WAIT / PASS"
            rationale = f"Price sits around historical medians (${stats.get('median_price')}). High likelihood of fare softening 6-8 weeks out."

        return {
            "verdict": verdict,
            "gotchas": gotchas,
            "positive_highlights": positives,
            "rationale": rationale
        }

    def audit_ticket(self, ticket: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits live concert and festival tickets, evaluating 25-30% junk service fees,
        resale floor markups, and obstructed view seats.
        """
        artist = ticket.get("artist")
        event_name = ticket.get("event_name")
        venue = ticket.get("venue")
        city = ticket.get("city")
        event_date = ticket.get("event_date")
        seat_type = ticket.get("seat_type")
        seat_detail = ticket.get("seat_detail")
        is_obstructed = ticket.get("is_obstructed", False)
        obstruction_detail = ticket.get("obstruction_detail", "")
        platform = ticket.get("platform")
        base_price = ticket.get("price")
        face_value = ticket.get("face_value", base_price)
        fee_rate = ticket.get("fee_rate", 0.28)
        junk_fee_amount = ticket.get("junk_fee_amount", round(base_price * fee_rate, 2))
        all_in_price = ticket.get("all_in_price", round(base_price + junk_fee_amount, 2))
        percentile = stats.get("percentile_rank", 50.0)
        savings = stats.get("estimated_savings", 0)

        prompt = f"""
You are the DealScout live music & ticketing intelligence engine. Audit this ticket quote:
- Artist / Event: {artist} ({event_name})
- Venue: {venue} in {city} ({event_date})
- Seat / Tier: {seat_type} ({seat_detail})
- Obstructed View: {"YES: " + obstruction_detail if is_obstructed else "NO - Clear Sightline"}
- Platform: {platform}
- Listed Base Price: ${base_price} (Face Value: ${face_value})
- Estimated Junk / Service Fee (+{round(fee_rate*100, 1)}%): +${junk_fee_amount}
- Total All-In Checkout Cost: ${all_in_price}
- Historical 90d Floor Percentile: {percentile}%

Evaluate this deal with acute vigilance:
1. All-In Junk Fee Audit: Secondary platforms (SeatGeek/Ticketmaster) slap 25-30% in hidden processing, facility, and digital delivery fees at checkout. Does the all-in total wipe out the apparent discount?
2. Sightline & Obstruction Check: Check if seat is flagged for obstructed views (e.g. pillars in historic venues like Georgia Theatre, side mezzanine angles, or distant soundboard towers in outdoor festivals like Shaky Knees in Central Park).
3. Value Verdict: Compare all-in checkout price vs face value and 90-day resale floor.

Return ONLY valid JSON matching this schema:
{{
  "verdict": "BUY NOW" | "FAIR VALUE" | "WAIT / PASS",
  "all_in_price": {all_in_price},
  "junk_fee_estimate": {junk_fee_amount},
  "fee_audit_note": "Short 1-sentence note quantifying how the +{round(fee_rate*100, 1)}% junk fee alters the true value.",
  "sightline_status": "CLEAR" | "OBSTRUCTED" | "STANDING_ROOM",
  "gotchas": ["list of fee caveats, transfer restrictions, or sightline notes"],
  "positive_highlights": ["list of positive aspects like general admission floor access, intimate venue, or below-face resale"],
  "rationale": "Crisp 2-sentence summary explaining whether to pull the trigger or hold out."
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
                print(f"[GeminiAuditor] Heuristic fallback for ticket {artist} ({e})")

        # Heuristic fallback
        gotchas = []
        positives = []

        gotchas.append(f"Checkout fee alert: +${junk_fee_amount:.2f} (+{round(fee_rate*100)}%) in service & facility fees added at final payment")

        if is_obstructed:
            gotchas.append(f"Obstructed view warning: {obstruction_detail}")
            sightline = "OBSTRUCTED"
        else:
            positives.append("Direct unobstructed sightline to main stage")
            sightline = "CLEAR" if "Floor" not in seat_type else "STANDING_ROOM"

        if all_in_price <= face_value * 1.05:
            positives.append(f"All-in price (${all_in_price:.2f}) beats or matches original face value (${face_value:.2f})")

        if percentile <= 20 and not is_obstructed:
            verdict = "BUY NOW"
            rationale = f"All-in price of ${all_in_price:.2f} sits at the bottom {percentile}% of recent resale quotes for {venue}. High demand event; grab before prices rebound."
        elif percentile <= 45 and not is_obstructed:
            verdict = "FAIR VALUE"
            rationale = f"Reasonable rate on {platform} with an all-in total of ${all_in_price:.2f}. Fair purchase if you want guaranteed entry."
        else:
            verdict = "WAIT / PASS"
            rationale = f"At ${all_in_price:.2f} all-in, secondary markups and 28% junk fees inflate this above target value. Recommend monitoring floor drops closer to show week."

        return {
            "verdict": verdict,
            "all_in_price": all_in_price,
            "junk_fee_estimate": junk_fee_amount,
            "fee_audit_note": f"+{round(fee_rate*100)}% fee adds ${junk_fee_amount:.2f} bringing true checkout total to ${all_in_price:.2f}.",
            "sightline_status": sightline,
            "gotchas": gotchas,
            "positive_highlights": positives,
            "rationale": rationale
        }

    def audit_product(self, product: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits consumer gear, outdoor apparel, footwear, boots, tech, and EDC.
        """
        name = product.get("name")
        category = product.get("category")
        retailer = product.get("retailer")
        variant = product.get("variant", "Standard")
        sale_tag = product.get("sale_tag", "")
        stock_status = product.get("stock_status", "In Stock")
        current_price = product.get("price")
        msrp = product.get("retail_msrp")
        target_price = product.get("target_price")
        specs = product.get("specs", "")
        percentile = stats.get("percentile_rank", 50.0)
        savings = stats.get("estimated_savings", 0)

        prompt = f"""
You are the DealScout consumer goods intelligence auditor. Analyze this retail deal:
- Item: {name} ({variant})
- Category: {category}
- Retailer / Vendor: {retailer}
- Current Deal Price: ${current_price} (Target: ${target_price}, List MSRP: ${msrp})
- Promotional Tag: {sale_tag} • Status: {stock_status}
- Specs & Materials: {specs}
- Historical 90d Percentile: {percentile}% (Calculated Savings vs Median: ${savings})

Evaluate authenticity, clearance validity, and product longevity:
1. For Patagonia Better Sweater, check if this qualifies for genuine end-of-season colorway clearance under $100 vs $159 MSRP across REI and Backcountry.
2. For Carhartt, verify heavy 12-oz duck canvas build and authentic workwear vs knockoff risk.
3. For Blundstone 500/550 Chelsea boots, check full-grain leather quality and sizing recommendations.
4. For athletic footwear (Nike GT Cut 3 / Adidas Samba), verify genuine colorway discounts vs deadstock markups.
5. For tech (Sony XM5 / Peak Design), verify authorized dealer warranty protection.

Return ONLY valid JSON matching this schema:
{{
  "verdict": "BUY NOW" | "FAIR VALUE" | "WAIT / PASS",
  "gotchas": ["list of caveats like final sale on seasonal colors, sizing quirks, or excluded coupon codes"],
  "positive_highlights": ["list of positive aspects like authorized retailer, lowest recorded price, durable materials"],
  "rationale": "Crisp 2-sentence summary explaining whether to pull the trigger or wait."
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
                print(f"[GeminiAuditor] Heuristic fallback for product {name} ({e})")

        # Heuristic fallback
        gotchas = []
        positives = [f"Sold by trusted authorized vendor ({retailer})", "Covered by manufacturer warranty"]

        if "Clearance" in sale_tag or "Seasonal" in variant:
            gotchas.append("Seasonal colorway markdown: verify return policy as clearance may be exchange-only")

        if "Blundstone" in name:
            positives.append("Premium water-resistant leather with XRD shock absorption")
            gotchas.append("Australian sizing: order half-size up for wider forefoot volume")
        elif "Patagonia" in name:
            if current_price < 100:
                positives.append(f"Rare sub-$100 threshold reached (${current_price} vs $159 MSRP)")
        elif "Carhartt" in name:
            positives.append("12-oz firm duck canvas with 3M Thinsulate insulation")
        elif "GT Cut" in name:
            positives.append("Elite ZoomX cushioning setup with premier lateral containment")
        elif "Samba" in name or "Gazelle" in name:
            positives.append("Timeless leather construction with durable gum rubber traction")
        elif "Sony" in name:
            positives.append("Industry-leading active noise canceling with dual processor setup")
        elif "Peak Design" in name:
            positives.append("Weatherproof 200D recycled nylon with origami pocket layout")

        if percentile <= 20 or current_price <= target_price:
            verdict = "BUY NOW"
            rationale = f"All-time competitive rate for {name} at ${current_price}, delivering approximately ${savings:.2f} savings vs median. Outstanding value."
        elif percentile <= 45:
            verdict = "FAIR VALUE"
            rationale = f"Solid promotional discount on {name} through {retailer}. Reliable buy if you need it immediately."
        else:
            verdict = "WAIT / PASS"
            rationale = f"Current price (${current_price}) hovers near typical market average. Recommend holding out for next seasonal promotional cycle."

        return {
            "verdict": verdict,
            "gotchas": gotchas,
            "positive_highlights": positives,
            "rationale": rationale
        }
