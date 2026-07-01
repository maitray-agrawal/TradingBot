"""System-wide enumerations for PrimeTrade AI.

This module provides Type-hinted Enumerations for standardizing variables across the
analytics, strategy, dashboard, and trading bot systems.
"""

from enum import Enum, unique


@unique
class Environment(str, Enum):
    """Execution environment settings."""

    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


@unique
class TradingSide(str, Enum):
    """Standardized trading directions."""

    BUY = "BUY"
    SELL = "SELL"


@unique
class OrderType(str, Enum):
    """Binance Futures order execution formats."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"


@unique
class DatasetType(str, Enum):
    """Supported datasets for analytics ingestion."""

    TRADER_HISTORY = "TRADER_HISTORY"
    FEAR_GREED = "FEAR_GREED"
    UNKNOWN = "UNKNOWN"


@unique
class SentimentRegime(str, Enum):
    """Fear & Greed Index categorization regimes."""

    EXTREME_FEAR = "Extreme Fear"
    FEAR = "Fear"
    NEUTRAL = "Neutral"
    GREED = "Greed"
    EXTREME_GREED = "Extreme Greed"

    @classmethod
    def from_value(cls, value: float) -> "SentimentRegime":
        """Maps numerical fear & greed value (0-100) to corresponding regime.

        Args:
            value: Numerical index score between 0 and 100.

        Returns:
            Corresponding SentimentRegime enum member.
        """
        if value < 25:
            return cls.EXTREME_FEAR
        elif value < 45:
            return cls.FEAR
        elif value < 55:
            return cls.NEUTRAL
        elif value < 75:
            return cls.GREED
        else:
            return cls.EXTREME_GREED


@unique
class StrategyAction(str, Enum):
    """Actions recommended by the strategy recommendation engine."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REDUCE_LEVERAGE = "Reduce Leverage"
    INCREASE_POSITION_SIZE = "Increase Position Size"
    AVOID_TRADING = "Avoid Trading"
