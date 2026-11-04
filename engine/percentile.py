"""
Statistical Percentile Engine for DealScout.
Calculates historical price envelopes, percentile rank, and detects true deal outliers.
"""

from __future__ import annotations
from typing import List, Dict, Any
import statistics

class PercentileEngine:
    @staticmethod
    def analyze_price(current_price: float, history: List[float]) -> Dict[str, Any]:
        """
        Analyzes a current price against historical time-series observations.
        
        Returns:
            Dict containing:
            - percentile_rank (0 to 100: lower means cheaper deal)
            - min_price
            - max_price
            - median_price
            - avg_price
            - price_score (0.00 to 1.00 normalized)
            - is_deal (True if percentile_rank <= 15.0)
            - tier ("STRONG BUY", "FAIR / AVERAGE", "OVERPRICED")
            - estimated_savings (vs median)
        """
        if not history:
            return {
                "percentile_rank": 50.0,
                "min_price": current_price,
                "max_price": current_price,
                "median_price": current_price,
                "avg_price": current_price,
                "price_score": 0.5,
                "is_deal": False,
                "tier": "INSUFFICIENT DATA",
                "estimated_savings": 0.0,
            }

        sorted_hist = sorted(history)
        n = len(sorted_hist)
        min_p = sorted_hist[0]
        max_p = sorted_hist[-1]
        med_p = statistics.median(sorted_hist)
        avg_p = statistics.mean(sorted_hist)

        # Percentile rank: fraction of historical prices that were strictly less than or equal to current price
        less_equal_count = sum(1 for p in sorted_hist if p <= current_price)
        percentile_rank = round((less_equal_count / n) * 100, 1)

        # Normalized Price Score in range [0, 1]
        if max_p > min_p:
            price_score = max(0.0, min(1.0, (current_price - min_p) / (max_p - min_p)))
        else:
            price_score = 0.5

        # Potential savings vs median
        savings = max(0.0, round(med_p - current_price, 2))

        # Deal classification
        if percentile_rank <= 15.0 or current_price <= min_p:
            tier = "STRONG BUY"
            is_deal = True
        elif percentile_rank <= 35.0:
            tier = "GOOD VALUE"
            is_deal = False
        elif percentile_rank <= 70.0:
            tier = "AVERAGE"
            is_deal = False
        else:
            tier = "OVERPRICED"
            is_deal = False

        return {
            "percentile_rank": percentile_rank,
            "min_price": round(min_p, 2),
            "max_price": round(max_p, 2),
            "median_price": round(med_p, 2),
            "avg_price": round(avg_p, 2),
            "price_score": round(price_score, 3),
            "is_deal": is_deal,
            "tier": tier,
            "estimated_savings": savings,
        }
