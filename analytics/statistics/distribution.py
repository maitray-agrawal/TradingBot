"""Distribution and normality testing module for PrimeTrade AI.

Applies Shapiro-Wilk, D'Agostino-Pearson K-Squared, and Kolmogorov-Smirnov (KS) tests
to check the distribution of returns and sentiment indices.
"""

from typing import Any, Dict

import numpy as np
import pandas as pd
from scipy import stats

from utils.logger import analytics_logger


class DistributionTester:
    """Performs statistical checks on sample distributions and normality assumptions."""

    @staticmethod
    def run_tests(df: pd.DataFrame) -> Dict[str, Any]:
        """Performs normality and two-sample KS distribution checks.

        Args:
            df: DataFrame containing the processed data.

        Returns:
            Dict[str, Any]: Test statistics, p-values, and normality outcomes.
        """
        analytics_logger.info("Executing distribution and normality tests...")
        results = {
            "pnl_normality": {
                "shapiro": {
                    "stat": None,
                    "p_value": None,
                    "normal": False,
                    "message": "No data",
                },
                "dagostino_k2": {
                    "stat": None,
                    "p_value": None,
                    "normal": False,
                    "message": "No data",
                },
                "ks_1sample": {
                    "stat": None,
                    "p_value": None,
                    "normal": False,
                    "message": "No data",
                },
            },
            "fg_normality": {
                "shapiro": {
                    "stat": None,
                    "p_value": None,
                    "normal": False,
                    "message": "No data",
                },
                "dagostino_k2": {
                    "stat": None,
                    "p_value": None,
                    "normal": False,
                    "message": "No data",
                },
                "ks_1sample": {
                    "stat": None,
                    "p_value": None,
                    "normal": False,
                    "message": "No data",
                },
            },
            "fear_vs_greed_ks_2samp": {
                "stat": None,
                "p_value": None,
                "same_distribution": False,
                "message": "No data",
            },
        }

        if df.empty:
            analytics_logger.warning("Empty DataFrame passed to DistributionTester.")
            return results

        # 1. Closed PnL Distribution Checks
        if "closed_pnl" in df.columns:
            pnl_data = df["closed_pnl"].dropna()
            results["pnl_normality"] = DistributionTester._test_normality(pnl_data, "closed_pnl")

        # 2. Fear & Greed Index Distribution Checks
        if "fg_value" in df.columns:
            fg_data = df["fg_value"].dropna()
            results["fg_normality"] = DistributionTester._test_normality(fg_data, "fg_value")

        # 3. Two-sample KS test comparing Fear vs Greed returns
        sentiment_col = (
            "fg_classification"
            if "fg_classification" in df.columns
            else ("classification" if "classification" in df.columns else None)
        )

        # Fallback grouping from fg_value if classification columns are missing
        df_temp = df.copy()
        if not sentiment_col and "fg_value" in df_temp.columns:
            df_temp["fg_classification"] = df_temp["fg_value"].apply(
                lambda val: "Fear" if val < 45 else ("Greed" if val > 55 else "Neutral")
            )
            sentiment_col = "fg_classification"

        if sentiment_col and "closed_pnl" in df_temp.columns:
            fear_regimes = ["Fear", "Extreme Fear"]
            greed_regimes = ["Greed", "Extreme Greed"]

            fear_pnl = df_temp[df_temp[sentiment_col].isin(fear_regimes)]["closed_pnl"].dropna()
            greed_pnl = df_temp[df_temp[sentiment_col].isin(greed_regimes)]["closed_pnl"].dropna()

            if len(fear_pnl) >= 2 and len(greed_pnl) >= 2:
                try:
                    ks_stat, ks_p = stats.ks_2samp(fear_pnl, greed_pnl)
                    results["fear_vs_greed_ks_2samp"] = {
                        "stat": float(ks_stat),
                        "p_value": float(ks_p),
                        "same_distribution": bool(ks_p >= 0.05),
                        "message": "Success",
                    }
                except Exception as e:
                    analytics_logger.error(f"Error running 2-sample KS test: {e}")
                    results["fear_vs_greed_ks_2samp"]["message"] = f"Execution error: {e}"
            else:
                results["fear_vs_greed_ks_2samp"]["message"] = "Requires at least 2 samples per regime."

        analytics_logger.info("Distribution testing complete.")
        return results

    @staticmethod
    def _test_normality(series: pd.Series, name: str) -> Dict[str, Any]:
        """Helper to run Shapiro-Wilk, D'Agostino-Pearson K2, and 1-sample KS tests on a single Series."""
        n = len(series)
        out = {
            "shapiro": {
                "stat": None,
                "p_value": None,
                "normal": False,
                "message": "No data",
            },
            "dagostino_k2": {
                "stat": None,
                "p_value": None,
                "normal": False,
                "message": "No data",
            },
            "ks_1sample": {
                "stat": None,
                "p_value": None,
                "normal": False,
                "message": "No data",
            },
        }

        if n < 3:
            msg = f"Insufficient sample size ({n}) for normality checks."
            out["shapiro"]["message"] = msg
            out["dagostino_k2"]["message"] = msg
            out["ks_1sample"]["message"] = msg
            return out

        # Shapiro-Wilk (limit 5000 in scipy for accuracy warning, but handles it)
        try:
            # For Shapiro-Wilk, if n is very large, sample 5000 to avoid scipy limits
            test_series = series.sample(5000, random_state=42) if n > 5000 else series
            sw_stat, sw_p = stats.shapiro(test_series)
            out["shapiro"] = {
                "stat": float(sw_stat),
                "p_value": float(sw_p),
                "normal": bool(sw_p >= 0.05),
                "message": "Success",
            }
        except Exception as e:
            analytics_logger.error(f"Shapiro-Wilk failed for {name}: {e}")
            out["shapiro"]["message"] = f"Error: {e}"

        # D'Agostino-Pearson K-Squared (Requires n >= 8)
        if n >= 8:
            try:
                k2_stat, k2_p = stats.normaltest(series)
                out["dagostino_k2"] = {
                    "stat": float(k2_stat),
                    "p_value": float(k2_p),
                    "normal": bool(k2_p >= 0.05),
                    "message": "Success",
                }
            except Exception as e:
                analytics_logger.error(f"D'Agostino-Pearson failed for {name}: {e}")
                out["dagostino_k2"]["message"] = f"Error: {e}"
        else:
            out["dagostino_k2"]["message"] = f"D'Agostino requires n >= 8 (current: {n})."

        # 1-sample KS test against standard normal distribution scaled by sample parameters
        try:
            mean = series.mean()
            std = series.std()
            if std > 0:
                ks_stat, ks_p = stats.kstest(series, "norm", args=(mean, std))
                out["ks_1sample"] = {
                    "stat": float(ks_stat),
                    "p_value": float(ks_p),
                    "normal": bool(ks_p >= 0.05),
                    "message": "Success",
                }
            else:
                out["ks_1sample"]["message"] = "Standard deviation is zero."
        except Exception as e:
            analytics_logger.error(f"1-sample KS test failed for {name}: {e}")
            out["ks_1sample"]["message"] = f"Error: {e}"

        return out
