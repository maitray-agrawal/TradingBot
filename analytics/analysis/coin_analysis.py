"""Asset performance and allocation analysis module for PrimeTrade AI.

Calculates detailed statistics, trading volumes, win/loss ratios,
drawdowns, custom risk scores, and performance rankings for each traded coin.
"""

from dataclasses import asdict, dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from utils.logger import analytics_logger


@dataclass
class CoinMetrics:
    """Performance statistics for a single cryptocurrency asset."""

    symbol: str
    trade_count: int
    total_pnl: float
    average_pnl: float
    median_pnl: float
    max_profit: float
    max_loss: float
    trade_volume: float
    average_trade_size: float
    win_rate: float
    risk_score: float
    rank: int


@dataclass
class CoinAnalysisResult:
    """Aggregated coin performance and rankings."""

    coins: Dict[str, Dict[str, Any]]
    ranked_coins_list: List[Dict[str, Any]]
    best_performing_coin: Optional[str]
    worst_performing_coin: Optional[str]


class CoinAnalysis:
    """Analyzes performance metrics, volume allocations, and risk scores across assets."""

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> CoinAnalysisResult:
        """Calculates per-asset trading stats, risk scores, and performance rankings.

        Args:
            df: Processed trading dataframe.

        Returns:
            CoinAnalysisResult: Ranks and profiles for all traded coins.
        """
        analytics_logger.info("Executing coin analysis module...")

        if df.empty:
            analytics_logger.warning("Empty dataframe provided to CoinAnalysis.")
            return CoinAnalysisResult(
                coins={},
                ranked_coins_list=[],
                best_performing_coin=None,
                worst_performing_coin=None,
            )

        if "symbol" not in df.columns:
            raise KeyError("Dataset is missing symbol column.")

        # Ensure trade_value exists
        df_copy = df.copy()
        if "trade_value" not in df_copy.columns:
            df_copy["trade_value"] = df_copy["size"] * df_copy["execution_price"]

        coin_profiles_list = []
        grouped = df_copy.groupby("symbol")

        for name, group in grouped:
            symbol = str(name)
            pnl_series = group["closed_pnl"].fillna(0.0)
            trade_count = len(group)
            total_pnl = float(pnl_series.sum())
            average_pnl = float(pnl_series.mean())
            median_pnl = float(pnl_series.median())
            max_profit = float(pnl_series.max())
            max_loss = float(pnl_series.min())

            trade_volume = float(group["trade_value"].fillna(0.0).sum())
            average_trade_size = (
                float(group["size"].mean()) if "size" in group.columns else 0.0
            )

            # Win Rate
            winning_trades = len(group[group["closed_pnl"] > 0])
            losing_trades = len(group[group["closed_pnl"] < 0])
            win_rate = winning_trades / trade_count if trade_count > 0 else 0.0
            loss_rate = losing_trades / trade_count if trade_count > 0 else 0.0

            # Custom Risk Score (0-100)
            loss_component = loss_rate * 60.0
            pnl_std = pnl_series.std() if len(pnl_series) > 1 else 0.0
            vol_mean = (
                group["trade_value"].mean() if not group["trade_value"].empty else 1.0
            )
            vol_mean = 1.0 if vol_mean == 0.0 else vol_mean

            pnl_vol_component = min(40.0, (pnl_std / vol_mean) * 40.0)
            risk_score = min(100.0, loss_component + pnl_vol_component)

            coin_profiles_list.append(
                {
                    "symbol": symbol,
                    "trade_count": trade_count,
                    "total_pnl": total_pnl,
                    "average_pnl": average_pnl,
                    "median_pnl": median_pnl,
                    "max_profit": max_profit,
                    "max_loss": max_loss,
                    "trade_volume": trade_volume,
                    "average_trade_size": average_trade_size,
                    "win_rate": win_rate,
                    "risk_score": risk_score,
                }
            )

        # Rank all coins by Total PnL descending
        coin_profiles_list.sort(key=lambda x: x["total_pnl"], reverse=True)

        ranked_coins = []
        coins_dict = {}

        for idx, profile in enumerate(coin_profiles_list):
            rank = idx + 1
            metrics = CoinMetrics(
                symbol=profile["symbol"],
                trade_count=profile["trade_count"],
                total_pnl=profile["total_pnl"],
                average_pnl=profile["average_pnl"],
                median_pnl=profile["median_pnl"],
                max_profit=profile["max_profit"],
                max_loss=profile["max_loss"],
                trade_volume=profile["trade_volume"],
                average_trade_size=profile["average_trade_size"],
                win_rate=profile["win_rate"],
                risk_score=profile["risk_score"],
                rank=rank,
            )

            metrics_dict = asdict(metrics)
            ranked_coins.append(metrics_dict)
            coins_dict[profile["symbol"]] = metrics_dict

        best_performing = ranked_coins[0]["symbol"] if ranked_coins else None
        worst_performing = ranked_coins[-1]["symbol"] if ranked_coins else None

        analytics_logger.info("Coin performance analysis completed.")
        return CoinAnalysisResult(
            coins=coins_dict,
            ranked_coins_list=ranked_coins,
            best_performing_coin=best_performing,
            worst_performing_coin=worst_performing,
        )
