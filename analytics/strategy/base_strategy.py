"""Abstract base strategy class for PrimeTrade AI.

This module provides the BaseStrategy class, which defines the interface for
all strategies and includes helper methods for calculating portfolio and risk metrics
(drawdown, win rate, trading frequency, and volatility) from historical trade data.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from config.enums import StrategyAction
from utils.logger import analytics_logger


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, name: str):
        """Initializes the strategy with a name.

        Args:
            name: Human-readable name of the strategy.
        """
        self.name = name

    @abstractmethod
    def generate_recommendation(
        self, df: pd.DataFrame, current_sentiment_val: Optional[float] = None
    ) -> Dict[str, Any]:
        """Evaluates market and portfolio metrics to generate a trading recommendation.

        Args:
            df: Historical and preprocessed trades DataFrame.
            current_sentiment_val: Optional latest Fear & Greed index value (0-100).
                If not provided, the strategy will fallback to the latest value in the df.

        Returns:
            Dict containing:
                - "action": StrategyAction enum value.
                - "confidence_score": float between 0.0 and 1.0.
                - "explanations": List[str] explaining the reasoning.
                - "metrics": Dict[str, Any] of computed metrics used in the decision.
        """
        pass

    def get_latest_sentiment(
        self, df: pd.DataFrame, current_sentiment_val: Optional[float] = None
    ) -> float:
        """Retrieves the latest sentiment score, prioritizing the external value.

        Args:
            df: Historical trades DataFrame.
            current_sentiment_val: Optional latest Fear & Greed index value.

        Returns:
            Sentiment value as a float. Defaults to 50.0 (Neutral) if not found.
        """
        if current_sentiment_val is not None:
            return float(current_sentiment_val)

        if not df.empty and "value" in df.columns:
            # "value" column contains Fear & Greed index from the merge
            return float(df["value"].iloc[-1])

        return 50.0

    def calculate_drawdown(
        self, df: pd.DataFrame, initial_balance: float = 10000.0
    ) -> Dict[str, float]:
        """Calculates current and maximum drawdown based on cumulative PnL.

        Args:
            df: Historical trades DataFrame.
            initial_balance: Initial account balance in USDT.

        Returns:
            Dict containing:
                - "current_drawdown": Current drawdown fraction (e.g., 0.05 for 5%).
                - "max_drawdown": Maximum drawdown fraction seen in history.
        """
        if df.empty:
            return {"current_drawdown": 0.0, "max_drawdown": 0.0}

        # Use cumulative PnL to compute historical balances
        cum_pnl = df["cumulative_pnl"] if "cumulative_pnl" in df.columns else df["closed_pnl"].cumsum()
        balances = initial_balance + cum_pnl

        # Prepend initial balance to handle start of series
        balances = pd.Series([initial_balance] + list(balances))

        peaks = balances.cummax()
        drawdowns = (peaks - balances) / peaks

        return {
            "current_drawdown": float(drawdowns.iloc[-1]),
            "max_drawdown": float(drawdowns.max()),
        }

    def calculate_rolling_win_rate(self, df: pd.DataFrame, window: int = 10) -> float:
        """Calculates the rolling win rate over the last N trades.

        Args:
            df: Historical trades DataFrame.
            window: Number of trades to calculate win rate over.

        Returns:
            Win rate fraction (0.0 to 1.0).
        """
        if df.empty:
            return 0.0

        target_col = "is_profit"
        if target_col not in df.columns:
            # Compute is_profit on the fly if missing
            is_profit = df["closed_pnl"] > 0
        else:
            is_profit = df[target_col]

        recent_trades = is_profit.tail(window)
        if len(recent_trades) == 0:
            return 0.0

        return float(recent_trades.mean())

    def calculate_trade_frequency(self, df: pd.DataFrame, window_days: int = 7) -> float:
        """Calculates average trade frequency (trades per day) over the last N days.

        Args:
            df: Historical trades DataFrame.
            window_days: Days window to look back from the latest trade.

        Returns:
            Average trades per day.
        """
        if df.empty or "timestamp" not in df.columns:
            return 0.0

        # Ensure timestamps are datetime
        timestamps = pd.to_datetime(df["timestamp"])
        latest_time = timestamps.max()
        cutoff_time = latest_time - pd.Timedelta(days=window_days)

        recent_trades = df[timestamps >= cutoff_time]
        return float(len(recent_trades) / max(window_days, 1))

    def calculate_volatility(self, df: pd.DataFrame, window: int = 10) -> float:
        """Calculates the standard deviation of recent trade returns.

        Args:
            df: Historical trades DataFrame.
            window: Number of trades to calculate volatility over.

        Returns:
            Standard deviation of closed PnL.
        """
        if df.empty or len(df) < 2:
            return 0.0

        recent_pnl = df["closed_pnl"].tail(window)
        return float(recent_pnl.std()) if len(recent_pnl) > 1 else 0.0
