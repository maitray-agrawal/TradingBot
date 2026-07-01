"""Market-wide analytics module for PrimeTrade AI.

Focuses on symbol distribution, trade side dynamics (BUY/SELL ratios),
volume concentration, and market-level statistics.
"""

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from utils.logger import analytics_logger


@dataclass
class MarketAnalysisResult:
    """Aggregated market analysis metrics."""

    symbol_distribution: Dict[str, int]
    side_distribution: Dict[str, int]
    volume_by_symbol: Dict[str, float]
    pnl_by_symbol: Dict[str, float]
    buy_sell_ratio: float
    volume_concentration_hhi: float
    top_traded_symbols: List[str]


class MarketAnalysis:
    """Performs global market allocation and trade activity distributions."""

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> MarketAnalysisResult:
        """Analyzes market-wide volume, side distributions, and asset concentrations.

        Args:
            df: Processed trading dataframe.

        Returns:
            MarketAnalysisResult: Structured object containing market-level analytics.
        """
        analytics_logger.info("Executing market analysis module...")

        if df.empty:
            analytics_logger.warning("Empty dataframe provided to MarketAnalysis.")
            return MarketAnalysisResult(
                symbol_distribution={},
                side_distribution={},
                volume_by_symbol={},
                pnl_by_symbol={},
                buy_sell_ratio=0.0,
                volume_concentration_hhi=0.0,
                top_traded_symbols=[],
            )

        # 1. Symbol distribution (Trade counts)
        symbol_counts = df["symbol"].value_counts().to_dict()

        # 2. Side distribution (BUY vs SELL)
        side_counts = df["side"].value_counts().to_dict()

        # 3. Volume and PnL by Symbol
        df_copy = df.copy()
        if "trade_value" not in df_copy.columns:
            df_copy["trade_value"] = df_copy["size"] * df_copy["execution_price"]

        volume_by_symbol = df_copy.groupby("symbol")["trade_value"].sum().to_dict()
        pnl_by_symbol = df_copy.groupby("symbol")["closed_pnl"].sum().to_dict()

        # Buy/Sell Ratio
        buys = side_counts.get("BUY", 0)
        sells = side_counts.get("SELL", 0)
        buy_sell_ratio = (
            buys / sells if sells > 0 else float("inf") if buys > 0 else 0.0
        )

        # Herfindahl-Hirschman Index (HHI) for Volume Concentration
        total_vol = sum(volume_by_symbol.values())
        hhi = 0.0
        if total_vol > 0:
            hhi = (
                sum((val / total_vol) ** 2 for val in volume_by_symbol.values()) * 10000
            )

        # Top traded symbols ranked by trade count
        top_symbols = sorted(
            symbol_counts.keys(), key=lambda x: symbol_counts[x], reverse=True
        )

        analytics_logger.info("Market analysis completed successfully.")
        return MarketAnalysisResult(
            symbol_distribution=symbol_counts,
            side_distribution=side_counts,
            volume_by_symbol=volume_by_symbol,
            pnl_by_symbol=pnl_by_symbol,
            buy_sell_ratio=buy_sell_ratio,
            volume_concentration_hhi=hhi,
            top_traded_symbols=top_symbols,
        )
