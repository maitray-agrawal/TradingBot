"""Descriptive statistics module for PrimeTrade AI.

Calculates basic statistical measures (mean, median, mode, variance, std, skewness,
kurtosis, quantiles) for numeric fields in the merged dataset.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from utils.logger import analytics_logger


class DescriptiveStatistics:
    """Calculates descriptive statistical metrics for numeric dataset columns."""

    @staticmethod
    def calculate(
        df: pd.DataFrame, columns: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Calculates descriptive statistics for target numeric columns in the dataframe.

        Args:
            df: DataFrame containing the processed/merged data.
            columns: Optional list of column names to analyze. If None, defaults
                     to ['closed_pnl', 'trade_value', 'size', 'fees', 'fg_value', 'profit_percentage'].

        Returns:
            Dict[str, Dict[str, Any]]: A nested dictionary mapping column names to
                                       their descriptive statistics.
        """
        analytics_logger.info("Calculating descriptive statistics...")
        results = {}

        if df.empty:
            analytics_logger.warning("Empty DataFrame passed to DescriptiveStatistics.")
            return results

        if columns is None:
            # Determine which columns exist in the DataFrame
            potential_cols = [
                "closed_pnl",
                "trade_value",
                "size",
                "fees",
                "fee",
                "fg_value",
                "profit_percentage",
            ]
            columns = [col for col in potential_cols if col in df.columns]

        for col in columns:
            if col not in df.columns:
                continue

            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if series.empty:
                continue

            # Calculate metrics
            mean_val = float(series.mean())
            median_val = float(series.median())

            # Mode calculation (can have multiple, take the first one or None)
            mode_series = series.mode()
            mode_val = float(mode_series.iloc[0]) if not mode_series.empty else None

            var_val = float(series.var()) if len(series) > 1 else 0.0
            std_val = float(series.std()) if len(series) > 1 else 0.0
            skew_val = float(series.skew()) if len(series) > 2 else 0.0
            kurt_val = float(series.kurt()) if len(series) > 3 else 0.0
            min_val = float(series.min())
            max_val = float(series.max())

            # Quantiles
            q25 = float(series.quantile(0.25))
            q50 = float(series.quantile(0.50))
            q75 = float(series.quantile(0.75))

            results[col] = {
                "mean": mean_val,
                "median": median_val,
                "mode": mode_val,
                "variance": var_val,
                "std_dev": std_val,
                "skewness": skew_val,
                "kurtosis": kurt_val,
                "min": min_val,
                "max": max_val,
                "quantile_25": q25,
                "quantile_50": q50,
                "quantile_75": q75,
                "count": len(series),
            }

        analytics_logger.info(
            f"Descriptive statistics calculated for {list(results.keys())}."
        )
        return results
