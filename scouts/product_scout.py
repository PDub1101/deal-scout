"""
Product Scout Module for DealScout.
Monitors wishlist gear, tech, and sports equipment across major retailers.
"""

from __future__ import annotations
import random
from typing import List, Dict, Any

class ProductScout:
    def fetch_quotes(self, watchlist_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetches current quotes for monitored wishlist gear.
        """
        quotes = []
        for item in watchlist_products:
            target = item.get("target_price", 100.0)
            msrp = item.get("retail_msrp", target * 1.3)

            # Realistic simulated market price with variance
            # Sometimes a genuine flash sale occurs (at or below target_price)
            roll = random.random()
            if roll < 0.25:
                # Genuine deal (below target)
                price = round(target * random.uniform(0.92, 0.99), 2)
                sale_tag = "FLASH DISCOUNT"
            elif roll < 0.65:
                # Normal street price
                price = round(target * random.uniform(1.05, 1.18), 2)
                sale_tag = "STANDARD STREET PRICE"
            else:
                # Near MSRP
                price = round(msrp * random.uniform(0.96, 1.0), 2)
                sale_tag = "LIST PRICE"

            quotes.append({
                "id": item["id"],
                "name": item["name"],
                "category": item.get("category", "General"),
                "price": price,
                "target_price": target,
                "retail_msrp": msrp,
                "retailer": item.get("retailer", "Major Retailer"),
                "sale_tag": sale_tag,
                "url": item.get("url", "#"),
            })

        return quotes
