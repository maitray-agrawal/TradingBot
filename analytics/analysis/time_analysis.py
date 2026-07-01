"""Time-series and periodic performance analysis module for PrimeTrade AI.

Breaks down trading activity and profitability by hourly intervals, weekday
vs weekends, quarterly cycles, and global trading sessions (Asia, Europe, America).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from typing import Any, Dict

import pandas as pd

from utils.logger import analytics_logger


@dataclass
class TimeAnalysisResult:
    """Breakdown of metrics across time and calendar intervals."""

    hourly_metrics: Dict[int, Dict[str, Any]]
    weekday_metrics: Dict[int, Dict[str, Any]]
    weekly_metrics: Dict[int, Dict[str, Any]]
    monthly_metrics: Dict[int, Dict[str, Any]]
    quarterly_metrics: Dict[int, Dict[str, Any]]
    weekend_vs_weekday: Dict[str, Dict[str, Any]]
    session_metrics: Dict[str, Dict[str, Any]]
    best_trading_hour: Optional[int]
    worst_trading_hour: Optional[int]


class TimeAnalysis:
    """Analyzes profitability trends, trade counts, and win rates across periods."""

    @staticmethod
    def _get_session(hour: int) -> str:
        """Determines the trading session (UTC) from the hour."""
        if 0 <= hour < 8:
            return "Asia"
        elif 8 <= hour < 16:
            return "Europe"
        else:
            return "America"

    @classmethod
    def calculate_metrics(cls, df: pd.DataFrame) -> TimeAnalysisResult:
        """Categorizes trade metrics based on chronological elements in the dataset.

        Args:
            df: Processed trading dataframe containing a 'timestamp' column.

        Returns:
            TimeAnalysisResult: Profitability breakdowns across multiple periodicities.
        """
        analytics_logger.info("Executing time analysis module...")

        if df.empty:
            analytics_logger.warning("Empty dataframe provided to TimeAnalysis.")
            return TimeAnalysisResult(
                hourly_metrics={},
                weekday_metrics={},
                weekly_metrics={},
                monthly_metrics={},
                quarterly_metrics={},
                weekend_vs_weekday={},
                session_metrics={},
                best_trading_hour=None,
                worst_trading_hour=None,
            )

        if "timestamp" not in df.columns:
            raise KeyError("Dataset is missing timestamp column.")

        df_copy = df.copy()

        # Ensure timestamp is datetime and timezone-naive
        df_copy["timestamp"] = pd.to_datetime(df_copy["timestamp"]).dt.tz_localize(None)

        # Extract features dynamically to guarantee presence and correctness
        df_copy["hour"] = df_copy["timestamp"].dt.hour
        df_copy["weekday"] = df_copy["timestamp"].dt.weekday
        df_copy["week"] = df_copy["timestamp"].dt.isocalendar().week.astype(int)
        df_copy["month"] = df_copy["timestamp"].dt.month
        df_copy["quarter"] = df_copy["timestamp"].dt.quarter
        df_copy["is_weekend"] = df_copy["weekday"].isin([5, 6]).map({True: "Weekend", False: "Weekday"})
        df_copy["session"] = df_copy["hour"].apply(cls._get_session)

        # Helper function to compute metrics for a group
        def calc_group_stats(grouped_df) -> Dict[Any, Dict[str, Any]]:
            res = {}
            for name, group in grouped_df:
                pnl = group["closed_pnl"].fillna(0.0)
                count = len(group)
                avg_pnl = float(pnl.mean())
                tot_pnl = float(pnl.sum())
                wins = len(group[group["closed_pnl"] > 0])
                win_rate = wins / count if count > 0 else 0.0
                res[name] = {
                    "trade_count": count,
                    "average_pnl": avg_pnl,
                    "total_pnl": tot_pnl,
                    "win_rate": win_rate,
                }
            return res

        hourly = calc_group_stats(df_copy.groupby("hour"))
        weekday = calc_group_stats(df_copy.groupby("weekday"))
        weekly = calc_group_stats(df_copy.groupby("week"))
        monthly = calc_group_stats(df_copy.groupby("month"))
        quarterly = calc_group_stats(df_copy.groupby("quarter"))
        weekend_vs_wk = calc_group_stats(df_copy.groupby("is_weekend"))
        sessions = calc_group_stats(df_copy.groupby("session"))

        # Find best and worst hours by average PnL
        best_hour = None
        worst_hour = None
        if hourly:
            best_hour = max(hourly.keys(), key=lambda h: hourly[h]["average_pnl"])
            worst_hour = min(hourly.keys(), key=lambda h: hourly[h]["average_pnl"])

        analytics_logger.info("Time-series analysis completed successfully.")
        return TimeAnalysisResult(
            hourly_metrics=hourly,
            weekday_metrics=weekday,
            weekly_metrics=weekly,
            monthly_metrics=monthly,
            quarterly_metrics=quarterly,
            weekend_vs_weekday=weekend_vs_wk,
            session_metrics=sessions,
            best_trading_hour=best_hour,
            worst_trading_hour=worst_hour,
        )
