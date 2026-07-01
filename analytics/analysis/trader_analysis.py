"""Trader behavior and performance analysis module for PrimeTrade AI.

Extracts stats per individual trader account, generates leaderboards,
and measures win/loss rates, trade frequencies, and custom risk scores.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from utils.logger import analytics_logger


@dataclass
class TraderMetrics:
    """Performance profile metrics for a single trader."""

    account_id: str
    total_pnl: float
    average_pnl: float
    median_pnl: float
    max_profit: float
    max_loss: float
    win_rate: float
    loss_rate: float
    trade_count: int
    total_volume: float
    risk_score: float


@dataclass
class TraderAnalysisResult:
    """Aggregated trader analysis results."""

    total_traders: int
    unique_traders: List[str]
    average_pnl_across_traders: float
    median_pnl_across_traders: float
    maximum_profit_trade: float
    maximum_loss_trade: float
    top_10_traders: List[Dict[str, Any]]
    bottom_10_traders: List[Dict[str, Any]]
    trader_metrics: Dict[str, Dict[str, Any]]


class TraderAnalysis:
    """Performs behavior, performance, and risk analysis on trader accounts."""

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> TraderAnalysisResult:
        """Calculates trader-level metrics and rankings from the processed dataset.

        Args:
            df: Processed trading dataframe.

        Returns:
            TraderAnalysisResult: Structured object containing calculated trader metrics.
        """
        analytics_logger.info("Executing trader analysis module...")

        if df.empty:
            analytics_logger.warning("Empty dataframe provided to TraderAnalysis.")
            return TraderAnalysisResult(
                total_traders=0,
                unique_traders=[],
                average_pnl_across_traders=0.0,
                median_pnl_across_traders=0.0,
                maximum_profit_trade=0.0,
                maximum_loss_trade=0.0,
                top_10_traders=[],
                bottom_10_traders=[],
                trader_metrics={},
            )

        # Ensure standard column name for account
        account_col = "account_id" if "account_id" in df.columns else ("account" if "account" in df.columns else None)
        if not account_col:
            raise KeyError("Dataset is missing account/account_id column.")

        unique_traders = df[account_col].dropna().unique().tolist()
        total_traders = len(unique_traders)

        # Base global trade-level max profit and loss
        maximum_profit_trade = float(df["closed_pnl"].max()) if "closed_pnl" in df.columns else 0.0
        maximum_loss_trade = float(df["closed_pnl"].min()) if "closed_pnl" in df.columns else 0.0

        trader_profiles: Dict[str, Dict[str, Any]] = {}
        trader_summary_list = []

        grouped = df.groupby(account_col)
        for name, group in grouped:
            account_id = str(name)
            pnl_series = group["closed_pnl"].fillna(0.0)
            trade_count = len(group)
            total_pnl = float(pnl_series.sum())
            average_pnl = float(pnl_series.mean())
            median_pnl = float(pnl_series.median())
            max_profit = float(pnl_series.max())
            max_loss = float(pnl_series.min())

            # Volume (trade_value = size * execution_price)
            vol_series = group["trade_value"] if "trade_value" in group.columns else (group["size"] * group["execution_price"])
            total_volume = float(vol_series.fillna(0.0).sum())

            # Win/Loss Rate: count wins vs losses
            winning_trades = len(group[group["closed_pnl"] > 0])
            losing_trades = len(group[group["closed_pnl"] < 0])

            win_rate = winning_trades / trade_count if trade_count > 0 else 0.0
            loss_rate = losing_trades / trade_count if trade_count > 0 else 0.0

            # Trader Risk Score:
            # 1. Loss Rate component: 60% weight
            loss_component = loss_rate * 60.0
            # 2. PnL Volatility relative to average trade value component: 40% weight
            avg_val = vol_series.mean() if not vol_series.empty else 0.0
            pnl_std = pnl_series.std() if len(pnl_series) > 1 else 0.0
            pnl_vol_component = 0.0
            if avg_val > 0:
                pnl_vol_component = min(40.0, (pnl_std / avg_val) * 40.0)

            risk_score = min(100.0, loss_component + pnl_vol_component)

            metrics = TraderMetrics(
                account_id=account_id,
                total_pnl=total_pnl,
                average_pnl=average_pnl,
                median_pnl=median_pnl,
                max_profit=max_profit,
                max_loss=max_loss,
                win_rate=win_rate,
                loss_rate=loss_rate,
                trade_count=trade_count,
                total_volume=total_volume,
                risk_score=risk_score,
            )

            trader_dict = asdict(metrics)
            trader_profiles[account_id] = trader_dict
            trader_summary_list.append(trader_dict)

        # Sort traders to generate Top 10 and Bottom 10 leaderboards
        sorted_traders = sorted(trader_summary_list, key=lambda x: x["total_pnl"], reverse=True)
        top_10 = sorted_traders[:10]
        bottom_10 = sorted_traders[::-1][:10]  # Reverse to get lowest PnL first

        # Global average/median PnL across traders
        trader_pnls = [t["total_pnl"] for t in trader_summary_list]
        average_pnl_across_traders = float(np.mean(trader_pnls)) if trader_pnls else 0.0
        median_pnl_across_traders = float(np.median(trader_pnls)) if trader_pnls else 0.0

        analytics_logger.info(f"Trader analysis completed for {total_traders} traders.")

        return TraderAnalysisResult(
            total_traders=total_traders,
            unique_traders=unique_traders,
            average_pnl_across_traders=average_pnl_across_traders,
            median_pnl_across_traders=median_pnl_across_traders,
            maximum_profit_trade=maximum_profit_trade,
            maximum_loss_trade=maximum_loss_trade,
            top_10_traders=top_10,
            bottom_10_traders=bottom_10,
            trader_metrics=trader_profiles,
        )
