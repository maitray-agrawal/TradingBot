"""Leaderboard plotting helper for PrimeTrade AI.

Contains functions to plot coin/symbol and trader leaderboard bar charts.
"""

from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.logger import analytics_logger


def plot_coin_leaderboard_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static horizontal bar chart of coin performance (by net PnL).

    Args:
        df: Processed DataFrame containing 'symbol' and 'closed_pnl'.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure, or None if required columns missing.
    """
    if "symbol" not in df.columns or "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'symbol' or 'closed_pnl' for coin leaderboard static plot.")
        return None

    # Group by symbol and get net PnL
    coin_perf = df.groupby("symbol")["closed_pnl"].sum().reset_index()
    coin_perf = coin_perf.sort_values("closed_pnl", ascending=True)  # Ascending for horizontal bar ordering

    if coin_perf.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Color code
    colors = ["#22C55E" if val >= 0 else "#EF4444" for val in coin_perf["closed_pnl"]]

    ax.barh(coin_perf["symbol"], coin_perf["closed_pnl"], color=colors, height=0.6)

    ax.set_title(
        "Performance Leaderboard by Asset Symbol",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Net Realized PnL (USDT)", fontsize=11, labelpad=10)
    ax.set_ylabel("Symbol", fontsize=11, labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.5, axis="x")

    # Reference line at x=0
    ax.axvline(0, color="gray", linewidth=0.8, linestyle="-")

    fig.tight_layout()
    return fig


def plot_coin_leaderboard_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive bar chart of coin rankings.

    Args:
        df: Processed DataFrame.

    Returns:
        Optional[go.Figure]: Plotly Figure, or None if required columns missing.
    """
    if "symbol" not in df.columns or "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'symbol' or 'closed_pnl' for coin leaderboard interactive plot.")
        return None

    coin_perf = df.groupby("symbol")["closed_pnl"].sum().reset_index()
    coin_perf = coin_perf.sort_values("closed_pnl", ascending=True)

    if coin_perf.empty:
        return None

    coin_perf["color"] = ["rgba(34, 197, 94, 0.85)" if p >= 0 else "rgba(239, 68, 68, 0.85)" for p in coin_perf["closed_pnl"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=coin_perf["symbol"],
            x=coin_perf["closed_pnl"],
            orientation="h",
            marker_color=coin_perf["color"],
            hovertemplate="<b>Symbol:</b> %{y}<br><b>Net Realized PnL:</b> %{x:.2f} USDT<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Performance Leaderboard by Asset Symbol",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        xaxis=dict(title="Net Realized PnL (USDT)", gridcolor="rgba(200, 200, 200, 0.15)"),
        yaxis=dict(title="Symbol"),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        plot_bgcolor="rgba(30, 41, 59, 1)",
        margin=dict(l=80, r=40, t=60, b=40),
        height=500,
    )
    return fig


def plot_trader_leaderboard_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static horizontal bar chart of trader account performance (by net PnL).

    Args:
        df: Processed DataFrame containing 'account_id' and 'closed_pnl'.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure, or None if required columns missing.
    """
    if "account_id" not in df.columns or "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'account_id' or 'closed_pnl' for trader leaderboard static plot.")
        return None

    trader_perf = df.groupby("account_id")["closed_pnl"].sum().reset_index()
    trader_perf = trader_perf.sort_values("closed_pnl", ascending=True)

    if trader_perf.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ["#22C55E" if val >= 0 else "#EF4444" for val in trader_perf["closed_pnl"]]

    ax.barh(trader_perf["account_id"], trader_perf["closed_pnl"], color=colors, height=0.6)

    ax.set_title(
        "Performance Leaderboard by Trader Account",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Net Realized PnL (USDT)", fontsize=11, labelpad=10)
    ax.set_ylabel("Account ID", fontsize=11, labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.5, axis="x")

    # Reference line at x=0
    ax.axvline(0, color="gray", linewidth=0.8, linestyle="-")

    fig.tight_layout()
    return fig


def plot_trader_leaderboard_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive bar chart of trader account rankings.

    Args:
        df: Processed DataFrame.

    Returns:
        Optional[go.Figure]: Plotly Figure, or None if required columns missing.
    """
    if "account_id" not in df.columns or "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'account_id' or 'closed_pnl' for trader leaderboard interactive plot.")
        return None

    trader_perf = df.groupby("account_id")["closed_pnl"].sum().reset_index()
    trader_perf = trader_perf.sort_values("closed_pnl", ascending=True)

    if trader_perf.empty:
        return None

    trader_perf["color"] = [
        "rgba(34, 197, 94, 0.85)" if p >= 0 else "rgba(239, 68, 68, 0.85)" for p in trader_perf["closed_pnl"]
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=trader_perf["account_id"],
            x=trader_perf["closed_pnl"],
            orientation="h",
            marker_color=trader_perf["color"],
            hovertemplate="<b>Account ID:</b> %{y}<br><b>Net Realized PnL:</b> %{x:.2f} USDT<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Performance Leaderboard by Trader Account",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        xaxis=dict(title="Net Realized PnL (USDT)", gridcolor="rgba(200, 200, 200, 0.15)"),
        yaxis=dict(title="Account ID"),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        plot_bgcolor="rgba(30, 41, 59, 1)",
        margin=dict(l=100, r=40, t=60, b=40),
        height=500,
    )
    return fig
