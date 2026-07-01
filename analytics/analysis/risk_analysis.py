"""Risk and exposure analytics module for PrimeTrade AI.

Calculates key risk parameters including peak-to-trough drawdowns,
historical Value at Risk (VaR), Expected Shortfall (ES),
Herfindahl-Hirschman trade value concentration, and composite risk scores.
"""

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from utils.logger import analytics_logger


@dataclass
class RiskAnalysisResult:
    """Detailed risk metrics and calculations."""

    max_drawdown: float
    average_drawdown: float
    pnl_volatility: float
    value_at_risk_95: float
    expected_shortfall_95: float
    top_3_profit_share: float
    top_3_loss_share: float
    trade_value_hhi: float
    composite_risk_score: float


class RiskAnalysis:
    """Performs drawdown, concentration, VaR, and risk score computations."""

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> RiskAnalysisResult:
        """Calculates advanced risk metrics from the processed trading history.

        Args:
            df: Processed trading dataframe.

        Returns:
            RiskAnalysisResult: Object containing drawdown, VaR, concentration, and risk score.
        """
        analytics_logger.info("Executing risk analysis module...")

        if df.empty:
            analytics_logger.warning("Empty dataframe provided to RiskAnalysis.")
            return RiskAnalysisResult(
                max_drawdown=0.0,
                average_drawdown=0.0,
                pnl_volatility=0.0,
                value_at_risk_95=0.0,
                expected_shortfall_95=0.0,
                top_3_profit_share=0.0,
                top_3_loss_share=0.0,
                trade_value_hhi=0.0,
                composite_risk_score=0.0,
            )

        pnl_series = df["closed_pnl"].fillna(0.0)

        # 1. Drawdown Calculations
        # Cumulative PnL trade-by-trade
        cum_pnl = pnl_series.cumsum()
        running_peak = cum_pnl.cummax()
        # If running peak is negative or starts at 0, handle it
        running_peak = np.maximum(running_peak, 0.0)
        drawdowns = running_peak - cum_pnl
        # Drawdowns are positive values representing loss from peak
        drawdowns = np.maximum(drawdowns, 0.0)

        max_drawdown = float(drawdowns.max())
        average_drawdown = float(drawdowns.mean())

        # 2. PnL Volatility (standard deviation of trade-by-trade closed PnL)
        pnl_volatility = float(pnl_series.std()) if len(pnl_series) > 1 else 0.0

        # 3. Value at Risk (Historical 95% Confidence Level)
        # Represents the 5th percentile of the trade PnL distribution
        value_at_risk_95 = float(pnl_series.quantile(0.05))

        # 4. Expected Shortfall (ES_95 / Conditional VaR)
        # Average of losses exceeding or equal to VaR
        losses_beyond_var = pnl_series[pnl_series <= value_at_risk_95]
        if not losses_beyond_var.empty:
            expected_shortfall_95 = float(losses_beyond_var.mean())
        else:
            expected_shortfall_95 = value_at_risk_95

        # 5. Trade Concentration
        gross_profit = float(pnl_series[pnl_series > 0].sum())
        gross_loss = float(pnl_series[pnl_series < 0].sum())

        best_trades = pnl_series.nlargest(3).tolist()
        worst_trades = pnl_series.nsmallest(3).tolist()

        top_3_profit_share = sum(best_trades) / gross_profit if gross_profit > 0 else 0.0
        top_3_loss_share = sum(abs(w) for w in worst_trades) / abs(gross_loss) if gross_loss < 0 else 0.0

        # HHI of trade values
        if "trade_value" not in df.columns:
            trade_values = (df["size"] * df["execution_price"]).fillna(0.0)
        else:
            trade_values = df["trade_value"].fillna(0.0)

        sum_trade_values = trade_values.sum()
        if sum_trade_values > 0:
            trade_value_hhi = float(sum((val / sum_trade_values) ** 2 for val in trade_values) * 10000)
        else:
            trade_value_hhi = 0.0

        # 6. Composite Risk Score (0-100 scale)
        # Component A: Win Rate penalty (0 to 40)
        # Lower win rate increases risk score.
        winning_count = len(pnl_series[pnl_series > 0])
        total_count = len(pnl_series)
        win_rate = winning_count / total_count if total_count > 0 else 0.0
        win_rate_penalty = (1.0 - win_rate) * 40.0

        # Component B: Drawdown Ratio penalty (0 to 30)
        # Max drawdown relative to absolute gross profit.
        drawdown_penalty = 0.0
        if gross_profit > 0:
            drawdown_penalty = min(30.0, (max_drawdown / gross_profit) * 30.0)
        elif max_drawdown > 0:
            drawdown_penalty = 30.0

        # Component C: PnL Volatility relative to average trade value (0 to 30)
        avg_trade_val = trade_values.mean() if not trade_values.empty else 1.0
        avg_trade_val = 1.0 if avg_trade_val == 0.0 else avg_trade_val
        volatility_penalty = min(30.0, (pnl_volatility / avg_trade_val) * 30.0)

        composite_risk_score = min(100.0, win_rate_penalty + drawdown_penalty + volatility_penalty)

        analytics_logger.info("Risk analysis completed successfully.")
        return RiskAnalysisResult(
            max_drawdown=max_drawdown,
            average_drawdown=average_drawdown,
            pnl_volatility=pnl_volatility,
            value_at_risk_95=value_at_risk_95,
            expected_shortfall_95=expected_shortfall_95,
            top_3_profit_share=top_3_profit_share,
            top_3_loss_share=top_3_loss_share,
            trade_value_hhi=trade_value_hhi,
            composite_risk_score=composite_risk_score,
        )
