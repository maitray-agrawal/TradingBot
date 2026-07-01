"""Feature correlation analysis module for PrimeTrade AI.

Computes Pearson and Spearman correlation matrices across numerical variables,
and quantifies linear/rank relationships between Fear & Greed, sizes, and PnL.
"""

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

from utils.logger import analytics_logger


@dataclass
class CorrelationAnalysisResult:
    """Correlation matrices and specific feature pairs."""

    pearson_matrix: Dict[str, Dict[str, float]]
    spearman_matrix: Dict[str, Dict[str, float]]
    sentiment_vs_pnl_pearson: float
    sentiment_vs_pnl_spearman: float
    size_vs_pnl_pearson: float
    fees_vs_pnl_pearson: float
    trade_frequency_vs_pnl_pearson: float


class CorrelationAnalysis:
    """Analyzes multivariate linear and monotonic dependencies in trade data."""

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> CorrelationAnalysisResult:
        """Computes correlation matrices and relationship strengths for key variables.

        Args:
            df: Processed trading dataframe.

        Returns:
            CorrelationAnalysisResult: Numerical correlations.
        """
        analytics_logger.info("Executing correlation analysis module...")

        if df.empty:
            analytics_logger.warning("Empty dataframe provided to CorrelationAnalysis.")
            return CorrelationAnalysisResult(
                pearson_matrix={},
                spearman_matrix={},
                sentiment_vs_pnl_pearson=0.0,
                sentiment_vs_pnl_spearman=0.0,
                size_vs_pnl_pearson=0.0,
                fees_vs_pnl_pearson=0.0,
                trade_frequency_vs_pnl_pearson=0.0,
            )

        df_copy = df.copy()

        # Ensure timestamp is datetime for daily aggregation
        df_copy["timestamp"] = pd.to_datetime(df_copy["timestamp"]).dt.tz_localize(None)

        # Ensure trade_value column
        if "trade_value" not in df_copy.columns:
            df_copy["trade_value"] = df_copy["size"] * df_copy["execution_price"]

        # Ensure hour and weekday features
        if "hour" not in df_copy.columns:
            df_copy["hour"] = df_copy["timestamp"].dt.hour
        if "weekday" not in df_copy.columns:
            df_copy["weekday"] = df_copy["timestamp"].dt.weekday

        # Numeric columns to include in matrices
        target_cols = [
            "execution_price",
            "size",
            "trade_value",
            "closed_pnl",
            "hour",
            "weekday",
        ]
        if "fg_value" in df_copy.columns and not df_copy["fg_value"].isna().all():
            target_cols.append("fg_value")

        fee_col = "fees" if "fees" in df_copy.columns else ("fee" if "fee" in df_copy.columns else None)
        if fee_col and not df_copy[fee_col].isna().all():
            target_cols.append(fee_col)

        # Filter df to numeric cols only and drop NaNs for correlation
        corr_df = df_copy[target_cols].dropna()

        pearson_mat = {}
        spearman_mat = {}

        if len(corr_df) > 1:
            pearson_mat = corr_df.corr(method="pearson").fillna(0.0).to_dict()
            spearman_mat = corr_df.corr(method="spearman").fillna(0.0).to_dict()

        # Target correlation pairs
        # 1. Sentiment vs PnL
        sentiment_vs_pnl_pearson = 0.0
        sentiment_vs_pnl_spearman = 0.0
        if "fg_value" in corr_df.columns:
            sentiment_vs_pnl_pearson = float(corr_df["fg_value"].corr(corr_df["closed_pnl"]))
            sentiment_vs_pnl_spearman = float(corr_df["fg_value"].corr(corr_df["closed_pnl"], method="spearman"))

        # 2. Size vs PnL
        size_vs_pnl_pearson = 0.0
        if "size" in corr_df.columns:
            size_vs_pnl_pearson = float(corr_df["size"].corr(corr_df["closed_pnl"]))

        # 3. Fees vs PnL
        fees_vs_pnl_pearson = 0.0
        if fee_col and fee_col in corr_df.columns:
            fees_vs_pnl_pearson = float(corr_df[fee_col].corr(corr_df["closed_pnl"]))

        # 4. Trade Frequency vs PnL (correlated daily trade count and daily closed PnL)
        trade_frequency_vs_pnl_pearson = 0.0
        df_copy["temp_date"] = df_copy["timestamp"].dt.date
        daily_stats = df_copy.groupby("temp_date").agg(trade_count=("closed_pnl", "count"), total_pnl=("closed_pnl", "sum"))
        if len(daily_stats) > 1:
            trade_frequency_vs_pnl_pearson = float(daily_stats["trade_count"].corr(daily_stats["total_pnl"]))

        # Clean up any nan values in scalars
        sentiment_vs_pnl_pearson = 0.0 if np.isnan(sentiment_vs_pnl_pearson) else sentiment_vs_pnl_pearson
        sentiment_vs_pnl_spearman = 0.0 if np.isnan(sentiment_vs_pnl_spearman) else sentiment_vs_pnl_spearman
        size_vs_pnl_pearson = 0.0 if np.isnan(size_vs_pnl_pearson) else size_vs_pnl_pearson
        fees_vs_pnl_pearson = 0.0 if np.isnan(fees_vs_pnl_pearson) else fees_vs_pnl_pearson
        trade_frequency_vs_pnl_pearson = 0.0 if np.isnan(trade_frequency_vs_pnl_pearson) else trade_frequency_vs_pnl_pearson

        analytics_logger.info("Correlation analysis completed successfully.")
        return CorrelationAnalysisResult(
            pearson_matrix=pearson_mat,
            spearman_matrix=spearman_mat,
            sentiment_vs_pnl_pearson=sentiment_vs_pnl_pearson,
            sentiment_vs_pnl_spearman=sentiment_vs_pnl_spearman,
            size_vs_pnl_pearson=size_vs_pnl_pearson,
            fees_vs_pnl_pearson=fees_vs_pnl_pearson,
            trade_frequency_vs_pnl_pearson=trade_frequency_vs_pnl_pearson,
        )
