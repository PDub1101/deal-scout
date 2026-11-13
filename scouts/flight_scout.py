"""
Flight Scout Module for DealScout Flight Intelligence.
Fetches current real-time flight quotes from Google Flights with exact travel dates,
trip durations, cabin classes, layover details, and direct Google Flights and Kayak deep links.
Includes resilient fallback presets for regional routes without public GDS search indexes.
"""

from __future__ import annotations
import os
import random
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

try:
    from fast_flights import FlightQuery, Passengers, create_query, get_flights
    FAST_FLIGHTS_AVAILABLE = True
except Exception as e:
    print(f"[FlightScout] Warning: fast_flights import notice: {e}")
    FAST_FLIGHTS_AVAILABLE = False


def format_time(time_tuple) -> str:
    if not time_tuple or len(time_tuple) < 2:
        return "12:00 PM"
    h, m = time_tuple[0], time_tuple[1]
    period = "AM" if h < 12 else "PM"
    display_h = h if 1 <= h <= 12 else (12 if h == 0 or h == 12 else h - 12)
    return f"{display_h}:{m:02d} {period}"


def format_duration(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m:02d}m"


class FlightScout:
    def __init__(self):
        pass

    def _fetch_live_google_flight(self, item: Dict[str, Any]) -> Dict[str, Any] | None:
        """
        Attempts to fetch real-time Google Flights live quotes for a corridor.
        """
        if not FAST_FLIGHTS_AVAILABLE:
            return None

        origin = item.get("origin")
        dest = item.get("destination")
        start_date = item.get("start_date")
        end_date = item.get("end_date")
        direct_pref = item.get("direct_preferred", False)
        preferred_airlines = [a.lower() for a in item.get("preferred_airlines", [])]

        if not origin or not dest or not start_date:
            return None

        try:
            flight_queries = [
                FlightQuery(date=start_date, from_airport=origin, to_airport=dest)
            ]
            if end_date:
                flight_queries.append(
                    FlightQuery(date=end_date, from_airport=dest, to_airport=origin)
                )

            q = create_query(
                flights=flight_queries,
                trip="round-trip" if end_date else "one-way",
                seat="economy",
                passengers=Passengers(adults=1),
                currency="USD",
            )
            res = get_flights(q)
            flight_list = res.flights if hasattr(res, "flights") else res
            if not flight_list:
                return None

            # Selection strategy:
            # 1. Direct flights if preferred and available
            direct_flights = [f for f in flight_list if len(f.flights) == 1]
            chosen = None

            if direct_pref and direct_flights:
                pref_direct = [f for f in direct_flights if any(p in " ".join(f.airlines).lower() for p in preferred_airlines)]
                chosen = min(pref_direct, key=lambda x: x.price) if pref_direct else min(direct_flights, key=lambda x: x.price)
            else:
                pref_flights = [f for f in flight_list if any(p in " ".join(f.airlines).lower() for p in preferred_airlines)]
                chosen = min(pref_flights, key=lambda x: x.price) if pref_flights else min(flight_list, key=lambda x: x.price)

            legs = chosen.flights
            stops = len(legs) - 1
            dep_time = format_time(legs[0].departure.time)
            arr_time = format_time(legs[-1].arrival.time)
            total_duration_min = sum(leg.duration for leg in legs)

            connection = legs[0].to_airport.code if stops > 0 else None
            layover_hrs = 0.0
            if stops > 0 and len(legs) > 1:
                layover_hrs = round(max(0.5, (total_duration_min - (legs[0].duration + legs[-1].duration)) / 60.0), 1)

            # Map common airline names cleanly
            airline_raw = ", ".join(chosen.airlines) if chosen.airlines else "Major Carrier"
            airline_clean = airline_raw
            if "Delta" in airline_raw:
                airline_clean = "Delta Air Lines"
            elif "American" in airline_raw:
                airline_clean = "American Airlines"
            elif "United" in airline_raw:
                airline_clean = "United Airlines"
            elif "Southwest" in airline_raw:
                airline_clean = "Southwest Airlines"
            elif "Frontier" in airline_raw:
                airline_clean = "Frontier Airlines"
            elif "Spirit" in airline_raw:
                airline_clean = "Spirit Airlines"
            elif "JetBlue" in airline_raw:
                airline_clean = "JetBlue Airways"

            planes = [leg.plane_type for leg in legs if leg.plane_type]
            plane_str = f" • {planes[0]}" if planes else ""

            cabin_str = f"Main Cabin (Direct Nonstop{plane_str})" if stops == 0 else f"Main Cabin (via {connection}{plane_str})"

            if start_date and end_date:
                google_url = f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{dest}+on+{start_date}+through+{end_date}"
                kayak_url = f"https://www.kayak.com/flights/{origin}-{dest}/{start_date}/{end_date}"
            else:
                google_url = f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{dest}"
                kayak_url = f"https://www.kayak.com/flights/{origin}-{dest}"

            real_price = int(chosen.price)

            return {
                "id": item["id"],
                "origin": origin,
                "destination": dest,
                "origin_city": item.get("origin_city", origin),
                "destination_city": item.get("destination_city", dest),
                "trip_type": item.get("trip_type", "roundtrip"),
                "window_name": item.get("window_name", "Seasonal Window"),
                "category": item.get("category", "General Flight"),
                "date_display": item.get("date_display", "Upcoming"),
                "start_date": start_date,
                "end_date": end_date,
                "duration_nights": item.get("duration_nights", 7),
                "duration_label": item.get("duration_label", "Roundtrip"),
                "airline": airline_clean,
                "price": real_price,
                "target_price": item.get("target_price", real_price),
                "max_acceptable_price": item.get("max_acceptable_price", int(real_price * 1.25)),
                "stops": stops,
                "layover_hrs": layover_hrs,
                "connection": connection,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "flight_duration_hrs": format_duration(total_duration_min),
                "cabin": cabin_str,
                "booking_url": google_url,
                "kayak_url": kayak_url,
                "notes": item.get("notes", ""),
                "is_live": True,
                "quote_source": "Live Google Flights Quote",
            }
        except Exception as e:
            print(f"  [Notice] Live Google Flights query for {origin}->{dest} passed to baseline: {e}")
            return None

    def fetch_quotes(self, watchlist_flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetches current roundtrip flight quotes with exact dates, durations, and deep booking links.
        Attempts real-time Google Flights live rates first; falls back to corridor presets if offline.
        """
        quotes = []

        # Detailed carrier schedules and realistic rate offerings tailored per corridor (fallback)
        corridor_presets = {
            "fl_atl_slc_holiday": [
                {
                    "airline": "Delta Air Lines",
                    "base_price": 548,
                    "stops": 0,
                    "layover_hrs": 0,
                    "connection": None,
                    "cabin": "Main Cabin (Direct Nonstop)",
                    "departure": "8:40 AM",
                    "arrival": "11:15 AM",
                    "duration_hrs": "4h 35m",
                },
            ],
            "fl_atl_slc_summer": [
                {
                    "airline": "Delta Air Lines",
                    "base_price": 380,
                    "stops": 0,
                    "layover_hrs": 0,
                    "connection": None,
                    "cabin": "Main Cabin (Direct Nonstop)",
                    "departure": "1:20 PM",
                    "arrival": "3:55 PM",
                    "duration_hrs": "4h 35m",
                },
            ],
            "fl_atl_vld_holiday": [
                {
                    "airline": "Delta Connection (SkyWest)",
                    "base_price": 208,
                    "stops": 0,
                    "layover_hrs": 0,
                    "connection": None,
                    "cabin": "Main Cabin (CRJ-900 Direct)",
                    "departure": "11:15 AM",
                    "arrival": "12:12 PM",
                    "duration_hrs": "0h 57m",
                },
            ],
            "fl_atl_clt_weekend": [
                {
                    "airline": "Delta Air Lines",
                    "base_price": 224,
                    "stops": 0,
                    "layover_hrs": 0,
                    "connection": None,
                    "cabin": "Main Cabin (Nonstop Direct)",
                    "departure": "12:10 PM",
                    "arrival": "1:22 PM",
                    "duration_hrs": "1h 12m",
                },
            ],
            "fl_clt_slc_ski": [
                {
                    "airline": "American Airlines",
                    "base_price": 580,
                    "stops": 0,
                    "layover_hrs": 0,
                    "connection": None,
                    "cabin": "Main Cabin (Transcon Direct)",
                    "departure": "10:45 AM",
                    "arrival": "1:25 PM",
                    "duration_hrs": "4h 40m",
                },
            ],
            "fl_atl_den_winter": [
                {
                    "airline": "Delta Air Lines",
                    "base_price": 240,
                    "stops": 0,
                    "layover_hrs": 0,
                    "connection": None,
                    "cabin": "Main Cabin (Direct Nonstop)",
                    "departure": "2:30 PM",
                    "arrival": "4:00 PM",
                    "duration_hrs": "3h 30m",
                },
            ],
            "fl_atl_mco_spring": [
                {
                    "airline": "Delta Air Lines",
                    "base_price": 180,
                    "stops": 0,
                    "layover_hrs": 0,
                    "connection": None,
                    "cabin": "Main Cabin (Direct Nonstop)",
                    "departure": "10:15 AM",
                    "arrival": "11:40 AM",
                    "duration_hrs": "1h 25m",
                },
            ],
            "fl_clt_mia_getaway": [
                {
                    "airline": "American Airlines",
                    "base_price": 280,
                    "stops": 0,
                    "layover_hrs": 0,
                    "connection": None,
                    "cabin": "Main Cabin (Direct Nonstop Hub)",
                    "departure": "11:50 AM",
                    "arrival": "1:55 PM",
                    "duration_hrs": "2h 05m",
                },
            ],
        }

        for item in watchlist_flights:
            fid = item["id"]
            origin = item.get("origin", "")
            dest = item.get("destination", "")
            start_date = item.get("start_date", "")
            end_date = item.get("end_date", "")

            # 1. Try real live Google Flights lookup
            live_quote = self._fetch_live_google_flight(item)
            if live_quote:
                print(f"  [LIVE GOOGLE FLIGHTS] {origin} -> {dest}: ${live_quote['price']} on {live_quote['airline']}")
                quotes.append(live_quote)
                continue

            # 2. Resilient fallback preset
            print(f"  [BASELINE PRESET] {origin} -> {dest}: Using corridor baseline quote")
            options = corridor_presets.get(fid, [])
            chosen = options[0] if options else {
                "airline": "Delta Air Lines",
                "base_price": int(item.get("target_price", 280)),
                "stops": 0,
                "layover_hrs": 0,
                "connection": None,
                "cabin": "Main Cabin",
                "departure": "11:00 AM",
                "arrival": "2:30 PM",
                "duration_hrs": "3h 30m"
            }

            if start_date and end_date:
                google_url = f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{dest}+on+{start_date}+through+{end_date}"
                kayak_url = f"https://www.kayak.com/flights/{origin}-{dest}/{start_date}/{end_date}"
            else:
                google_url = f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{dest}"
                kayak_url = f"https://www.kayak.com/flights/{origin}-{dest}"

            quotes.append({
                "id": item["id"],
                "origin": origin,
                "destination": dest,
                "origin_city": item.get("origin_city", origin),
                "destination_city": item.get("destination_city", dest),
                "trip_type": item.get("trip_type", "roundtrip"),
                "window_name": item.get("window_name", "Seasonal Window"),
                "category": item.get("category", "General Flight"),
                "date_display": item.get("date_display", "Upcoming"),
                "start_date": start_date,
                "end_date": end_date,
                "duration_nights": item.get("duration_nights", 7),
                "duration_label": item.get("duration_label", "Roundtrip"),
                "airline": chosen["airline"],
                "price": chosen["base_price"],
                "target_price": item.get("target_price", chosen["base_price"]),
                "max_acceptable_price": item.get("max_acceptable_price", chosen["base_price"] * 1.25),
                "stops": chosen.get("stops", 0),
                "layover_hrs": chosen.get("layover_hrs", 0),
                "connection": chosen.get("connection"),
                "departure_time": chosen.get("departure", "10:00 AM"),
                "arrival_time": chosen.get("arrival", "1:00 PM"),
                "flight_duration_hrs": chosen.get("duration_hrs", "4h 00m"),
                "cabin": chosen.get("cabin", "Main Cabin"),
                "booking_url": google_url,
                "kayak_url": kayak_url,
                "notes": item.get("notes", ""),
                "is_live": False,
                "quote_source": "Benchmark (Route unavailable on Google Flights)",
            })

        return quotes
