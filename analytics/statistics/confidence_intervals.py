"""Confidence intervals module for PrimeTrade AI.

Calculates statistical confidence intervals (e.g., 95% levels) for trade win rates,
average PnL, and average trade sizes.
"""

from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from utils.logger import analytics_logger


class ConfidenceIntervals:
    """Calculates confidence intervals for key performance metrics."""

    @staticmethod
    def calculate(df: pd.DataFrame, confidence: float = 0.95) -> Dict[str, Dict[str, Any]]:
        """Calculates confidence intervals for win rate, mean PnL, and mean size.

        Args:
            df: DataFrame containing the processed data.
            confidence: Level of confidence, e.g., 0.95 for 95% intervals.

        Returns:
            Dict[str, Dict[str, Any]]: Confidence intervals containing mean/proportion estimates,
                                       lower bound, upper bound, and margin of error.
        """
        analytics_logger.info(f"Calculating {confidence*100}% confidence intervals...")
        results = {}

        if df.empty:
            analytics_logger.warning("Empty DataFrame passed to ConfidenceIntervals.")
            return results

        # 1. Win Rate Confidence Interval (Wilson Score Interval for Binomial Proportion)
        if "closed_pnl" in df.columns:
            pnl_series = df["closed_pnl"].dropna()
            n = len(pnl_series)
            if n > 0:
                wins = int((pnl_series > 0).sum())
                p = wins / n

                # Wilson Score Interval
                try:
                    z = float(stats.norm.ppf(1 - (1 - confidence) / 2))
                    denom = 1 + (z**2) / n
                    center = (p + (z**2) / (2 * n)) / denom
                    spread = z * np.sqrt((p * (1 - p)) / n + (z**2) / (4 * n**2)) / denom

                    lower = float(max(0.0, center - spread))
                    upper = float(min(1.0, center + spread))
                    margin_error = float(spread)

                    results["win_rate"] = {
                        "estimate": p,
                        "lower_bound": lower,
                        "upper_bound": upper,
                        "margin_of_error": margin_error,
                        "sample_size": n,
                        "method": "Wilson Score",
                    }
                except Exception as e:
                    analytics_logger.error(f"Error computing win rate CI: {e}")

        # 2. Average PnL Confidence Interval (Student's t interval for mean)
        if "closed_pnl" in df.columns:
            pnl_series = df["closed_pnl"].dropna()
            n = len(pnl_series)
            if n >= 2:
                try:
                    mean_val = float(pnl_series.mean())
                    sem = float(stats.sem(pnl_series))

                    if sem > 0:
                        lower, upper = stats.t.interval(confidence, df=n - 1, loc=mean_val, scale=sem)
                        margin_error = float(upper - mean_val)
                    else:
                        lower, upper, margin_error = mean_val, mean_val, 0.0

                    results["average_pnl"] = {
                        "estimate": mean_val,
                        "lower_bound": float(lower),
                        "upper_bound": float(upper),
                        "margin_of_error": float(margin_error),
                        "sample_size": n,
                        "method": "Student-t",
                    }
                except Exception as e:
                    analytics_logger.error(f"Error computing average PnL CI: {e}")

        # 3. Average Trade Size Confidence Interval (Student's t interval for mean)
        size_col = "size" if "size" in df.columns else None
        if size_col:
            size_series = df[size_col].dropna()
            n = len(size_series)
            if n >= 2:
                try:
                    mean_val = float(size_series.mean())
                    sem = float(stats.sem(size_series))

                    if sem > 0:
                        lower, upper = stats.t.interval(confidence, df=n - 1, loc=mean_val, scale=sem)
                        margin_error = float(upper - mean_val)
                    else:
                        lower, upper, margin_error = mean_val, mean_val, 0.0

                    results["average_trade_size"] = {
                        "estimate": mean_val,
                        "lower_bound": float(lower),
                        "upper_bound": float(upper),
                        "margin_of_error": float(margin_error),
                        "sample_size": n,
                        "method": "Student-t",
                    }
                except Exception as e:
                    analytics_logger.error(f"Error computing average trade size CI: {e}")

        analytics_logger.info("Confidence intervals calculations completed.")
        return results
