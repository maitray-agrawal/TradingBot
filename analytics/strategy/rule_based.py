"""Rule-based strategy implementation for PrimeTrade AI.

This module contains the RuleBasedStrategy class, which uses portfolio risk metrics,
rolling performance, trade frequency, and market sentiment (Fear & Greed)
to generate actionable trading recommendations with confidence scores and explanations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, Field

from analytics.strategy.base_strategy import BaseStrategy
from config.enums import StrategyAction


class StrategyConfig(BaseModel):
    """Pydantic model representing strategy configuration parameters."""

    max_drawdown_threshold: float = Field(
        default=0.15,
        description="Maximum drawdown percentage (0.15 = 15%) before triggering Avoid Trading.",
    )
    min_rolling_win_rate: float = Field(
        default=0.45,
        description="Minimum rolling win rate below which leverage is reduced.",
    )
    overtrading_frequency_limit: float = Field(
        default=10.0,
        description="Limit on trades per day over the last N days before triggering Avoid Trading.",
    )
    fear_greed_buy_threshold: float = Field(
        default=25.0,
        description="Fear & Greed Index score below which represents an accumulation/buying regime.",
    )
    fear_greed_sell_threshold: float = Field(
        default=75.0,
        description="Fear & Greed Index score above which represents a distribution/selling regime.",
    )
    initial_balance: float = Field(
        default=10000.0,
        description="Initial balance in USDT to calculate drawdown metrics.",
    )
    rolling_window: int = Field(
        default=10,
        description="Window size for rolling statistics (win rate, volatility).",
    )
    frequency_window_days: int = Field(
        default=7,
        description="Window in days to compute trade frequency.",
    )


class StrategyRecommendation(BaseModel):
    """Pydantic model representing the output of a strategy evaluation."""

    action: StrategyAction = Field(..., description="The recommended action.")
    confidence_score: float = Field(
        ...,
        description="Confidence score between 0.0 and 1.0.",
        ge=0.0,
        le=1.0,
    )
    explanations: List[str] = Field(
        default_factory=list,
        description="Natural language reasons explaining the recommendation.",
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Historical and risk metrics computed during evaluation.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Timestamp of recommendation generation.",
    )


class RuleBasedStrategy(BaseStrategy):
    """A highly configurable rule-based trading strategy."""

    def __init__(
        self,
        name: str = "Rule-Based Sentiment & Risk Strategy",
        config: Optional[StrategyConfig] = None,
    ):
        """Initializes the strategy with configuration.

        Args:
            name: Name of the strategy.
            config: Optional StrategyConfig instance. If None, default config is used.
        """
        super().__init__(name)
        self.config = config or StrategyConfig()

    def generate_recommendation(
        self, df: pd.DataFrame, current_sentiment_val: Optional[float] = None
    ) -> Dict[str, Any]:
        """Evaluates market and portfolio metrics to generate a trading recommendation.

        Args:
            df: Historical and preprocessed trades DataFrame.
            current_sentiment_val: Optional latest Fear & Greed index value (0-100).

        Returns:
            Dict containing serialized StrategyRecommendation.
        """
        explanations: List[str] = []
        metrics: Dict[str, Any] = {}

        if df.empty:
            rec = StrategyRecommendation(
                action=StrategyAction.HOLD,
                confidence_score=0.50,
                explanations=["No trade history available. Holding active action."],
                metrics={"current_drawdown": 0.0, "rolling_win_rate": 0.0},
            )
            return rec.model_dump()

        # 1. Compute metrics
        sentiment_val = self.get_latest_sentiment(df, current_sentiment_val)
        drawdowns = self.calculate_drawdown(df, self.config.initial_balance)
        current_dd = drawdowns["current_drawdown"]
        max_dd = drawdowns["max_drawdown"]
        rolling_win_rate = self.calculate_rolling_win_rate(
            df, window=self.config.rolling_window
        )
        trade_freq = self.calculate_trade_frequency(
            df, window_days=self.config.frequency_window_days
        )
        volatility = self.calculate_volatility(df, window=self.config.rolling_window)

        # Store calculated metrics for transparency
        metrics.update(
            {
                "fear_greed_score": sentiment_val,
                "current_drawdown": round(current_dd, 4),
                "max_drawdown": round(max_dd, 4),
                "rolling_win_rate": round(rolling_win_rate, 4),
                "trades_per_day": round(trade_freq, 2),
                "recent_volatility": round(volatility, 4),
            }
        )

        # 2. Check Rules in Order of Priority

        # Rule Category 1: AVOID TRADING (Capital Preservation)
        avoid_reasons = []
        if current_dd >= self.config.max_drawdown_threshold:
            avoid_reasons.append(
                f"Current drawdown ({current_dd:.2%}) meets or exceeds maximum risk threshold ({self.config.max_drawdown_threshold:.2%})."
            )
        if rolling_win_rate < 0.30 and len(df) >= self.config.rolling_window:
            avoid_reasons.append(
                f"Recent rolling win rate ({rolling_win_rate:.2%}) is critically underperforming (under 30%)."
            )
        if trade_freq >= self.config.overtrading_frequency_limit:
            avoid_reasons.append(
                f"Trading frequency ({trade_freq:.1f} trades/day) meets or exceeds overtrading threshold ({self.config.overtrading_frequency_limit:.1f} trades/day)."
            )

        if avoid_reasons:
            explanations.extend(avoid_reasons)
            explanations.append("Trading activity is restricted to preserve capital.")
            rec = StrategyRecommendation(
                action=StrategyAction.AVOID_TRADING,
                confidence_score=0.90,
                explanations=explanations,
                metrics=metrics,
            )
            return rec.model_dump()

        # Rule Category 2: REDUCE LEVERAGE (Risk De-escalation)
        reduce_reasons = []
        if rolling_win_rate < self.config.min_rolling_win_rate and len(df) >= self.config.rolling_window:
            reduce_reasons.append(
                f"Rolling win rate ({rolling_win_rate:.2%}) has dropped below minimum threshold ({self.config.min_rolling_win_rate:.2%})."
            )
        if current_dd >= 0.08:
            reduce_reasons.append(
                f"Drawdown is elevated at {current_dd:.2%}, requiring exposure reduction."
            )
        if volatility > 200.0:  # Custom volatility threshold for high-variance periods
            reduce_reasons.append(
                f"Recent trade volatility ({volatility:.2f}) is elevated."
            )

        if reduce_reasons:
            explanations.extend(reduce_reasons)
            explanations.append(
                "Recommend lowering execution leverage to minimize variance."
            )
            rec = StrategyRecommendation(
                action=StrategyAction.REDUCE_LEVERAGE,
                confidence_score=0.80,
                explanations=explanations,
                metrics=metrics,
            )
            return rec.model_dump()

        # Rule Category 3: Sentiment & Opportunity Signals
        # A. Extreme Fear -> BUY Opportunity (Contrarian)
        if sentiment_val < self.config.fear_greed_buy_threshold:
            explanations.append(
                f"Fear & Greed Index is at {sentiment_val:.0f} (Extreme Fear), indicating a potential market bottom."
            )
            # Add boost to confidence if win rate is good
            confidence = 0.70 + min((25.0 - sentiment_val) / 100.0, 0.20)
            if rolling_win_rate > 0.55:
                confidence = min(confidence + 0.05, 0.95)
                explanations.append("Strategy confidence is supported by a stable rolling win rate.")

            rec = StrategyRecommendation(
                action=StrategyAction.BUY,
                confidence_score=round(confidence, 2),
                explanations=explanations,
                metrics=metrics,
            )
            return rec.model_dump()

        # B. Extreme Greed -> SELL / Take Profit Opportunity
        if sentiment_val >= self.config.fear_greed_sell_threshold:
            explanations.append(
                f"Fear & Greed Index is at {sentiment_val:.0f} (Extreme Greed), indicating a potential market top."
            )
            confidence = 0.70 + min((sentiment_val - 75.0) / 100.0, 0.20)
            rec = StrategyRecommendation(
                action=StrategyAction.SELL,
                confidence_score=round(confidence, 2),
                explanations=explanations,
                metrics=metrics,
            )
            return rec.model_dump()

        # C. Compounding -> Increase Position Size
        if rolling_win_rate >= 0.60 and current_dd < 0.04 and 45.0 <= sentiment_val < 75.0:
            explanations.append(
                f"Strong rolling win rate ({rolling_win_rate:.2%}) combined with minor drawdown ({current_dd:.2%}) and stable trend sentiment ({sentiment_val:.0f})."
            )
            explanations.append("Recommend increasing position sizing to compound gains.")
            rec = StrategyRecommendation(
                action=StrategyAction.INCREASE_POSITION_SIZE,
                confidence_score=0.85,
                explanations=explanations,
                metrics=metrics,
            )
            return rec.model_dump()

        # D. Neutral State -> HOLD
        explanations.append(
            f"Market sentiment is neutral ({sentiment_val:.0f}) and account risk parameters are within normal bounds."
        )
        rec = StrategyRecommendation(
            action=StrategyAction.HOLD,
            confidence_score=0.60,
            explanations=explanations,
            metrics=metrics,
        )
        return rec.model_dump()
