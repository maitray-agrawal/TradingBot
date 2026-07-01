"""Correlation analysis module for PrimeTrade AI.

Computes Pearson, Spearman, and Kendall rank correlations and their p-values
between sentiment index (Fear & Greed) and trading outcomes (PnL, size, fees, holding time).
"""

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from utils.logger import analytics_logger


class CorrelationCalculator:
    """Computes correlation coefficients and significance levels for trading and sentiment data."""

    @staticmethod
    def calculate_correlations(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Calculates Pearson, Spearman, and Kendall correlations for target pairs.

        Args:
            df: DataFrame containing the processed data.

        Returns:
            Dict[str, Dict[str, Any]]: Correlation results including coefficients,
                                       p-values, and statistical significance statements.
        """
        analytics_logger.info("Computing statistical correlations...")
        results = {}

        if df.empty:
            analytics_logger.warning("Empty DataFrame passed to CorrelationCalculator.")
            return results

        # Create temporary holding time column if entry/exit columns exist
        df_temp = df.copy()
        if "entry_timestamp" in df_temp.columns and "exit_timestamp" in df_temp.columns:
            try:
                entry = pd.to_datetime(df_temp["entry_timestamp"])
                exit_t = pd.to_datetime(df_temp["exit_timestamp"])
                df_temp["holding_time_seconds"] = (exit_t - entry).dt.total_seconds()
            except Exception as e:
                analytics_logger.warning(
                    f"Could not compute holding time for correlation: {e}"
                )

        # Target pairs to correlate with 'fg_value' (Fear & Greed Index value)
        if "fg_value" not in df_temp.columns:
            analytics_logger.warning(
                "Fear & Greed Index ('fg_value') not present in data."
            )
            return results

        target_vars = [
            "closed_pnl",
            "trade_value",
            "size",
            "fees",
            "fee",
            "holding_time_seconds",
            "profit_percentage",
        ]
        active_vars = [var for var in target_vars if var in df_temp.columns]

        for var in active_vars:
            # Pairwise dropna for current variable and fg_value
            pair_df = df_temp[["fg_value", var]].dropna()

            # Check size constraints
            if len(pair_df) < 3:
                analytics_logger.warning(
                    f"Insufficient data points ({len(pair_df)}) for correlating fg_value vs {var}."
                )
                continue

            x = pair_df["fg_value"]
            y = pair_df[var]

            # Check for zero variance
            if x.std() == 0 or y.std() == 0:
                analytics_logger.warning(
                    f"Zero variance in either fg_value or {var}. Skipping correlation."
                )
                continue

            # Pearson
            try:
                pearson_coef, pearson_p = stats.pearsonr(x, y)
            except Exception as e:
                analytics_logger.error(
                    f"Pearson calculation failed for fg_value vs {var}: {e}"
                )
                pearson_coef, pearson_p = np.nan, np.nan

            # Spearman
            try:
                spearman_res = stats.spearmanr(x, y)
                spearman_coef, spearman_p = spearman_res.statistic, spearman_res.pvalue
            except Exception as e:
                analytics_logger.error(
                    f"Spearman calculation failed for fg_value vs {var}: {e}"
                )
                spearman_coef, spearman_p = np.nan, np.nan

            # Kendall
            try:
                kendall_res = stats.kendalltau(x, y)
                kendall_coef, kendall_p = kendall_res.correlation, kendall_res.pvalue
            except Exception as e:
                analytics_logger.error(
                    f"Kendall calculation failed for fg_value vs {var}: {e}"
                )
                kendall_coef, kendall_p = np.nan, np.nan

            results[f"fg_value_vs_{var}"] = {
                "pearson": {
                    "coefficient": (
                        float(pearson_coef) if not np.isnan(pearson_coef) else None
                    ),
                    "p_value": float(pearson_p) if not np.isnan(pearson_p) else None,
                    "significant": (
                        bool(pearson_p < 0.05) if not np.isnan(pearson_p) else False
                    ),
                },
                "spearman": {
                    "coefficient": (
                        float(spearman_coef) if not np.isnan(spearman_coef) else None
                    ),
                    "p_value": float(spearman_p) if not np.isnan(spearman_p) else None,
                    "significant": (
                        bool(spearman_p < 0.05) if not np.isnan(spearman_p) else False
                    ),
                },
                "kendall": {
                    "coefficient": (
                        float(kendall_coef) if not np.isnan(kendall_coef) else None
                    ),
                    "p_value": float(kendall_p) if not np.isnan(kendall_p) else None,
                    "significant": (
                        bool(kendall_p < 0.05) if not np.isnan(kendall_p) else False
                    ),
                },
                "sample_size": len(pair_df),
            }

        analytics_logger.info("Correlation calculations finished.")
        return results
