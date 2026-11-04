"""
Product Scout Module for DealScout.
Monitors curated apparel, footwear, boots, tech, and EDC gear across major retailers:
- Patagonia Better Sweater 1/4-Zip Fleece (end-of-season colorway clearance under $100 vs $159 MSRP across REI and Backcountry)
- Carhartt Duck Canvas Active Jacket / WIP
- Blundstone 500 / 550 Chelsea Boots
- Basketball & Soccer Footwear: Nike Basketball (GT Cut series) and Adidas classics (Samba / Gazelle)
- Tech & EDC: Sony WH-1000XM5 ANC Headphones and Peak Design Tech Pouch
"""

from __future__ import annotations
import random
from typing import List, Dict, Any

class ProductScout:
    def fetch_quotes(self, watchlist_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetches current quotes for monitored apparel, footwear, tech, and EDC gear.
        """
        quotes = []

        product_presets = {
            "prod_patagonia_better_sweater": [
                {
                    "variant": "End-of-Season Colorway Clearance (Wavy Blue / Basin Green)",
                    "retailer": "REI Co-op Outlet",
                    "price_factor": 0.59,  # ~ $93.80 (Under $100 vs $159 MSRP)
                    "sale_tag": "SEASONAL CLEARANCE (<$100)",
                    "stock_status": "In Stock (Sizes M, L, XL)",
                },
                {
                    "variant": "Discontinued Seasonal Hue (Pewter Stone)",
                    "retailer": "Backcountry",
                    "price_factor": 0.62,  # ~ $98.50
                    "sale_tag": "BACKCOUNTRY FLASH SALE",
                    "stock_status": "Low Stock (3 left)",
                },
                {
                    "variant": "Core Colorway (Black / Stonewash)",
                    "retailer": "Patagonia Official",
                    "price_factor": 1.0,  # $159.00
                    "sale_tag": "CORE FULL PRICE",
                    "stock_status": "Full Stock",
                },
            ],
            "prod_carhartt_active_jacket": [
                {
                    "variant": "Loose Fit Firm Duck Insulated (Carhartt Brown)",
                    "retailer": "Dungarees Workwear",
                    "price_factor": 0.76,  # ~$98.80 (Below target $99)
                    "sale_tag": "FACTORY OVERSTOCK DEAL",
                    "stock_status": "In Stock",
                },
                {
                    "variant": "Loose Fit Firm Duck Insulated (Black / Dark Navy)",
                    "retailer": "Carhartt Online",
                    "price_factor": 0.92,
                    "sale_tag": "SEASONAL WORKWEAR",
                    "stock_status": "In Stock",
                },
            ],
            "prod_blundstone_550": [
                {
                    "variant": "Classic 550 Chelsea Boot (Rustic Brown)",
                    "retailer": "REI Co-op Member Sale",
                    "price_factor": 0.72,  # ~$165.50 vs $229.95 MSRP
                    "sale_tag": "20% ANNIVERSARY COUPON ELIGIBLE",
                    "stock_status": "In Stock (Full Size Run)",
                },
                {
                    "variant": "Classic 500 Series (Stout Brown)",
                    "retailer": "Backcountry",
                    "price_factor": 0.85,
                    "sale_tag": "STANDARD OUTDOOR RETAIL",
                    "stock_status": "In Stock",
                },
            ],
            "prod_nike_gt_cut": [
                {
                    "variant": "Nike G.T. Cut 3 (Summit White / Laser Orange)",
                    "retailer": "Nike Store Member Pass",
                    "price_factor": 0.66,  # ~$125.40 vs $190 MSRP
                    "sale_tag": "NIKE APP FLASH DISCOUNT",
                    "stock_status": "In Stock (Men's 9.5-12)",
                },
                {
                    "variant": "Nike G.T. Cut Cross (Black / Bright Crimson)",
                    "retailer": "Dick's Sporting Goods",
                    "price_factor": 0.82,
                    "sale_tag": "COURT PROMO",
                    "stock_status": "In Stock",
                },
            ],
            "prod_adidas_samba_gazelle": [
                {
                    "variant": "Adidas Samba OG (Cloud White / Core Black / Gum)",
                    "retailer": "Adidas Official / Confirmed",
                    "price_factor": 0.74,  # ~$74.00 vs $100 MSRP
                    "sale_tag": "ADI-CLUB REWARD DISCOUNT",
                    "stock_status": "In Stock",
                },
                {
                    "variant": "Adidas Gazelle Classic (Collegiate Navy / White)",
                    "retailer": "Nordstrom",
                    "price_factor": 0.78,
                    "sale_tag": "SEASONAL RESTOCK SPECIAL",
                    "stock_status": "In Stock",
                },
            ],
            "prod_sony_xm5": [
                {
                    "variant": "Sony WH-1000XM5 Wireless Headphones (Midnight Blue / Silver)",
                    "retailer": "Best Buy / Amazon",
                    "price_factor": 0.745,  # ~$298.00 vs $399.99 MSRP
                    "sale_tag": "PRIME / PRICE MATCH PROMO",
                    "stock_status": "Authorized Dealer New in Box",
                },
                {
                    "variant": "Sony WH-1000XM5 (Black)",
                    "retailer": "B&H Photo Video",
                    "price_factor": 0.87,
                    "sale_tag": "AUTHORIZED RETAIL",
                    "stock_status": "In Stock",
                },
            ],
            "prod_peak_design_tech_pouch": [
                {
                    "variant": "Peak Design Tech Pouch V1/V2 (Black / Charcoal)",
                    "retailer": "Peak Design / B&H Photo",
                    "price_factor": 0.75,  # ~$48.70 vs $64.95 MSRP
                    "sale_tag": "HOLIDAY BUNDLE CLEARANCE",
                    "stock_status": "In Stock",
                },
                {
                    "variant": "Peak Design Tech Pouch (Midnight Blue)",
                    "retailer": "REI Co-op",
                    "price_factor": 0.92,
                    "sale_tag": "REI CO-OP STANDARD",
                    "stock_status": "In Stock",
                },
            ],
        }

        for item in watchlist_products:
            pid = item["id"]
            msrp = item.get("retail_msrp", 100.0)
            target = item.get("target_price", 80.0)
            options = product_presets.get(pid)

            if options:
                # 35% chance of picking prime deal preset
                chosen = random.choice(options)
                price = round(msrp * chosen["price_factor"], 2)
                # Small jitter
                price = max(19.0, round(price + random.uniform(-1.5, 1.5), 2))
                retailer = chosen["retailer"]
                variant = chosen["variant"]
                sale_tag = chosen["sale_tag"]
                stock_status = chosen["stock_status"]
            else:
                roll = random.random()
                if roll < 0.3:
                    price = round(target * random.uniform(0.92, 0.99), 2)
                    sale_tag = "FLASH DISCOUNT"
                else:
                    price = round(target * random.uniform(1.05, 1.18), 2)
                    sale_tag = "STANDARD STREET"
                retailer = item.get("retailer", "Major Retailer")
                variant = "Standard Edition"
                stock_status = "In Stock"

            quotes.append({
                "id": item["id"],
                "name": item["name"],
                "category": item.get("category", "General"),
                "price": price,
                "target_price": target,
                "retail_msrp": msrp,
                "retailer": retailer,
                "variant": variant,
                "sale_tag": sale_tag,
                "stock_status": stock_status,
                "specs": item.get("specs", ""),
                "url": item.get("url", "#"),
            })

        return quotes
