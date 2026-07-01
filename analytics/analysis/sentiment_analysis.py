"""Fear & Greed Sentiment analysis module for PrimeTrade AI.

Classifies and groups historical trades by Fear & Greed regimes, and
computes statistical averages, win rates, loss rates, and trade size metrics.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config.enums import SentimentRegime
from utils.logger import analytics_logger


@dataclass
class SentimentRegimeMetrics:
    """Metrics calculated for a specific sentiment regime."""

    regime: str
    trade_count: int
    average_pnl: float
    median_pnl: float
    average_trade_value: float
    average_position_size: float
    win_rate: float
    loss_rate: float
    average_fees: float


@dataclass
class SentimentAnalysisResult:
    """Aggregated sentiment analysis results."""

    regimes: Dict[str, Dict[str, Any]]
    dominant_regime: Optional[str]
    best_performing_regime: Optional[str]
    worst_performing_regime: Optional[str]


class SentimentAnalysis:
    """Analyzes trader performance metrics relative to the Fear & Greed index regimes."""

    @staticmethod
    def _map_row_to_regime(row: pd.Series) -> Optional[str]:
        """Maps a dataframe row to a standardized SentimentRegime string."""
        # 1. Prioritize numerical score fg_value
        if "fg_value" in row and pd.notna(row["fg_value"]):
            try:
                val = float(row["fg_value"])
                return SentimentRegime.from_value(val).value
            except (ValueError, TypeError):
                pass

        # 2. Fall back to fg_classification string
        if "fg_classification" in row and pd.notna(row["fg_classification"]):
            class_str = str(row["fg_classification"]).strip().title()
            for r in SentimentRegime:
                if r.value == class_str:
                    return r.value
                # Match common variants (e.g. ExtremeFear -> Extreme Fear)
                if (
                    r.value.replace(" ", "").lower()
                    == class_str.replace(" ", "").lower()
                ):
                    return r.value

        return None

    @classmethod
    def calculate_metrics(cls, df: pd.DataFrame) -> SentimentAnalysisResult:
        """Categorizes trade results by Fear & Greed index regimes.

        Args:
            df: Processed trading dataframe with merged sentiment values.

        Returns:
            SentimentAnalysisResult: Performance metrics per regime.
        """
        analytics_logger.info("Executing sentiment analysis module...")

        if df.empty:
            analytics_logger.warning("Empty dataframe provided to SentimentAnalysis.")
            return SentimentAnalysisResult(
                regimes={},
                dominant_regime=None,
                best_performing_regime=None,
                worst_performing_regime=None,
            )

        df_copy = df.copy()

        # Map each row to a regime
        df_copy["mapped_regime"] = df_copy.apply(cls._map_row_to_regime, axis=1)

        # Filter out rows with no valid regime classification
        valid_df = df_copy[df_copy["mapped_regime"].notna()]

        if valid_df.empty:
            analytics_logger.warning("No trades with valid sentiment mapping found.")
            return SentimentAnalysisResult(
                regimes={},
                dominant_regime=None,
                best_performing_regime=None,
                worst_performing_regime=None,
            )

        regimes_dict: Dict[str, Dict[str, Any]] = {}

        # Ensure trade_value column exists
        if "trade_value" not in valid_df.columns:
            valid_df["trade_value"] = valid_df["size"] * valid_df["execution_price"]

        # Default fee column check
        fee_col = (
            "fees"
            if "fees" in valid_df.columns
            else ("fee" if "fee" in valid_df.columns else None)
        )

        grouped = valid_df.groupby("mapped_regime")
        for name, group in grouped:
            regime_name = str(name)
            trade_count = len(group)

            pnl_series = group["closed_pnl"].fillna(0.0)
            avg_pnl = float(pnl_series.mean())
            med_pnl = float(pnl_series.median())

            avg_val = (
                float(group["trade_value"].mean())
                if "trade_value" in group.columns
                else 0.0
            )
            avg_size = float(group["size"].mean()) if "size" in group.columns else 0.0

            # Win/Loss Rate
            winning_trades = len(group[group["closed_pnl"] > 0])
            losing_trades = len(group[group["closed_pnl"] < 0])

            win_rate = winning_trades / trade_count if trade_count > 0 else 0.0
            loss_rate = losing_trades / trade_count if trade_count > 0 else 0.0

            # Average Fees
            avg_fees = (
                float(group[fee_col].mean())
                if fee_col and not group[fee_col].isna().all()
                else 0.0
            )

            metrics = SentimentRegimeMetrics(
                regime=regime_name,
                trade_count=trade_count,
                average_pnl=avg_pnl,
                median_pnl=med_pnl,
                average_trade_value=avg_val,
                average_position_size=avg_size,
                win_rate=win_rate,
                loss_rate=loss_rate,
                average_fees=avg_fees,
            )

            regimes_dict[regime_name] = asdict(metrics)

        # Compute dominant, best performing, and worst performing regimes
        dominant_regime = (
            max(regimes_dict.keys(), key=lambda k: regimes_dict[k]["trade_count"])
            if regimes_dict
            else None
        )

        # Best and worst based on average PnL
        best_regime = (
            max(regimes_dict.keys(), key=lambda k: regimes_dict[k]["average_pnl"])
            if regimes_dict
            else None
        )
        worst_regime = (
            min(regimes_dict.keys(), key=lambda k: regimes_dict[k]["average_pnl"])
            if regimes_dict
            else None
        )

        analytics_logger.info("Sentiment analysis completed successfully.")
        return SentimentAnalysisResult(
            regimes=regimes_dict,
            dominant_regime=dominant_regime,
            best_performing_regime=best_regime,
            worst_performing_regime=worst_regime,
        )
