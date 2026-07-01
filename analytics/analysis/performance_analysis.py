"""System-wide trading performance statistics module for PrimeTrade AI.

Calculates aggregated metrics such as win/loss/breakeven counts, gross profit,
gross loss, net profit, profit factor, average trade sizes, and average fees.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from utils.logger import analytics_logger


@dataclass
class PerformanceAnalysisResult:
    """Aggregated trade performance results."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate: float
    loss_rate: float
    average_trade_size: float
    average_trade_value: float
    average_holding_time_seconds: Optional[float]
    average_fee: float
    net_profit: float
    gross_profit: float
    gross_loss: float
    profit_factor: float


class PerformanceAnalysis:
    """Performs aggregate-level trading performance and efficiency checks."""

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> PerformanceAnalysisResult:
        """Calculates system-wide trading statistics, win rates, and profit factors.

        Args:
            df: Processed trading dataframe.

        Returns:
            PerformanceAnalysisResult: Aggregated trading metrics.
        """
        analytics_logger.info("Executing performance analysis module...")

        if df.empty:
            analytics_logger.warning("Empty dataframe provided to PerformanceAnalysis.")
            return PerformanceAnalysisResult(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                breakeven_trades=0,
                win_rate=0.0,
                loss_rate=0.0,
                average_trade_size=0.0,
                average_trade_value=0.0,
                average_holding_time_seconds=None,
                average_fee=0.0,
                net_profit=0.0,
                gross_profit=0.0,
                gross_loss=0.0,
                profit_factor=0.0,
            )

        total_trades = len(df)

        # Calculate winning, losing, and breakeven trades
        pnl_series = df["closed_pnl"].fillna(0.0)
        winning_trades = int((pnl_series > 0).sum())
        losing_trades = int((pnl_series < 0).sum())
        breakeven_trades = int((pnl_series == 0).sum())

        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        loss_rate = losing_trades / total_trades if total_trades > 0 else 0.0

        # Trade size (quantity) and Trade value (size * execution_price)
        average_trade_size = float(df["size"].mean()) if "size" in df.columns else 0.0

        if "trade_value" in df.columns:
            average_trade_value = float(df["trade_value"].mean())
        elif "size" in df.columns and "execution_price" in df.columns:
            average_trade_value = float((df["size"] * df["execution_price"]).mean())
        else:
            average_trade_value = 0.0

        # Holding Time Analysis (if entry and exit timestamps exist)
        avg_holding_time = None
        if "entry_timestamp" in df.columns and "exit_timestamp" in df.columns:
            try:
                entry = pd.to_datetime(df["entry_timestamp"])
                exit_t = pd.to_datetime(df["exit_timestamp"])
                durations = (exit_t - entry).dt.total_seconds()
                avg_holding_time = float(durations.mean())
            except Exception as e:
                analytics_logger.warning(f"Error calculating average holding time: {e}")

        # Fee calculations
        fee_col = (
            "fees" if "fees" in df.columns else ("fee" if "fee" in df.columns else None)
        )
        average_fee = (
            float(df[fee_col].mean())
            if fee_col and not df[fee_col].isna().all()
            else 0.0
        )

        # Profits and Losses
        net_profit = float(pnl_series.sum())
        gross_profit = float(pnl_series[pnl_series > 0].sum())
        gross_loss = float(pnl_series[pnl_series < 0].sum())  # Typically negative

        # Profit Factor: Gross Profit / absolute(Gross Loss)
        abs_gross_loss = abs(gross_loss)
        if abs_gross_loss > 0:
            profit_factor = gross_profit / abs_gross_loss
        else:
            # If there's profit and no loss, profit factor is infinite (we represent as 999.99 for display)
            profit_factor = 999.99 if gross_profit > 0 else 0.0

        analytics_logger.info("Performance analysis completed successfully.")
        return PerformanceAnalysisResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            breakeven_trades=breakeven_trades,
            win_rate=win_rate,
            loss_rate=loss_rate,
            average_trade_size=average_trade_size,
            average_trade_value=average_trade_value,
            average_holding_time_seconds=avg_holding_time,
            average_fee=average_fee,
            net_profit=net_profit,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
        )
