"""Timeseries plotting helper for PrimeTrade AI.

Contains functions to plot cumulative PnL and daily realized PnL using
both static (Matplotlib) and interactive (Plotly) libraries.
"""

from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.logger import analytics_logger


def plot_cumulative_pnl_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static line chart of cumulative PnL over time.

    Args:
        df: Processed DataFrame containing 'timestamp' and 'closed_pnl'.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure object, or None if required columns missing.
    """
    if "timestamp" not in df.columns or "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'timestamp' or 'closed_pnl' for cumulative PnL static plot.")
        return None

    # Ensure chronological order
    data = df.sort_values("timestamp").copy()
    data["cum_pnl"] = data["closed_pnl"].cumsum()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Render line with fill below it
    ax.plot(
        data["timestamp"],
        data["cum_pnl"],
        color="#0052CC",
        linewidth=2.0,
        label="Cumulative PnL",
    )
    ax.fill_between(data["timestamp"], data["cum_pnl"], color="#0052CC", alpha=0.1)

    # Styling
    ax.set_title("Cumulative PnL Over Time", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Time", fontsize=11, labelpad=10)
    ax.set_ylabel("PnL (USDT)", fontsize=11, labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")

    # Rotate x labels for readability
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    return fig


def plot_cumulative_pnl_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive line chart of cumulative PnL.

    Args:
        df: Processed DataFrame containing 'timestamp' and 'closed_pnl'.

    Returns:
        Optional[go.Figure]: Plotly Figure object, or None if required columns missing.
    """
    if "timestamp" not in df.columns or "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'timestamp' or 'closed_pnl' for cumulative PnL interactive plot.")
        return None

    data = df.sort_values("timestamp").copy()
    data["cum_pnl"] = data["closed_pnl"].cumsum()

    fig = go.Figure()

    # Area chart with gradient fill
    fig.add_trace(
        go.Scatter(
            x=data["timestamp"],
            y=data["cum_pnl"],
            mode="lines",
            name="Cumulative PnL",
            line=dict(color="#0052CC", width=3),
            fill="tozeroy",
            fillcolor="rgba(0, 82, 204, 0.1)",
            hovertemplate="<b>Date:</b> %{x}<br><b>Cumulative PnL:</b> %{y:.2f} USDT<extra></extra>",
        )
    )

    # Modern Dark/Glassmorphic look
    fig.update_layout(
        title=dict(
            text="Cumulative PnL Over Time",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        xaxis=dict(
            title="Time",
            gridcolor="rgba(200, 200, 200, 0.15)",
            rangeslider=dict(visible=True),  # Interactive range slider
            type="date",
        ),
        yaxis=dict(title="PnL (USDT)", gridcolor="rgba(200, 200, 200, 0.15)"),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",  # Slate 900
        plot_bgcolor="rgba(30, 41, 59, 1)",  # Slate 800
        margin=dict(l=40, r=40, t=60, b=40),
        height=600,
    )
    return fig


def plot_daily_pnl_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static bar chart of daily realized PnL.

    Args:
        df: Processed DataFrame containing 'timestamp' and 'closed_pnl'.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure object, or None if required columns missing.
    """
    if "timestamp" not in df.columns or "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'timestamp' or 'closed_pnl' for daily PnL static plot.")
        return None

    # Aggregate by date
    data = df.copy()
    data["date"] = pd.to_datetime(data["timestamp"]).dt.date
    daily_pnl = data.groupby("date")["closed_pnl"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Color code positive and negative days
    colors = ["#22C55E" if pnl >= 0 else "#EF4444" for pnl in daily_pnl["closed_pnl"]]

    ax.bar(
        daily_pnl["date"],
        daily_pnl["closed_pnl"],
        color=colors,
        width=0.6,
        edgecolor="none",
    )

    ax.set_title("Daily Realized PnL", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Date", fontsize=11, labelpad=10)
    ax.set_ylabel("PnL (USDT)", fontsize=11, labelpad=10)
    ax.grid(True, linestyle="--", alpha=0.5, axis="y")

    # Rotate labels
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    # Draw reference line at y=0
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="-")

    fig.tight_layout()
    return fig


def plot_daily_pnl_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive bar chart of daily realized PnL.

    Args:
        df: Processed DataFrame containing 'timestamp' and 'closed_pnl'.

    Returns:
        Optional[go.Figure]: Plotly Figure object, or None if required columns missing.
    """
    if "timestamp" not in df.columns or "closed_pnl" not in df.columns:
        analytics_logger.warning("Missing 'timestamp' or 'closed_pnl' for daily PnL interactive plot.")
        return None

    # Aggregate by date
    data = df.copy()
    data["date"] = pd.to_datetime(data["timestamp"]).dt.date
    daily_pnl = data.groupby("date")["closed_pnl"].sum().reset_index()

    # Color code
    daily_pnl["color"] = ["rgba(34, 197, 94, 0.85)" if p >= 0 else "rgba(239, 68, 68, 0.85)" for p in daily_pnl["closed_pnl"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=daily_pnl["date"],
            y=daily_pnl["closed_pnl"],
            marker_color=daily_pnl["color"],
            hovertemplate="<b>Date:</b> %{x}<br><b>Net PnL:</b> %{y:.2f} USDT<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Daily Realized PnL",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        xaxis=dict(title="Date", gridcolor="rgba(200, 200, 200, 0.15)", type="category"),
        yaxis=dict(title="PnL (USDT)", gridcolor="rgba(200, 200, 200, 0.15)"),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        plot_bgcolor="rgba(30, 41, 59, 1)",
        margin=dict(l=40, r=40, t=60, b=40),
        height=500,
    )
    return fig
