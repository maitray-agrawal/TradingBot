"""Heatmap plotting helper for PrimeTrade AI.

Contains functions to plot hourly UTC session activity heatmaps.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

from utils.logger import analytics_logger


def plot_hourly_activity_matplotlib(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generates a static heatmap representing average PnL or trade frequency by UTC Hour and Weekday.

    Args:
        df: Processed DataFrame containing 'hour', 'weekday' and 'closed_pnl'.

    Returns:
        Optional[plt.Figure]: Matplotlib Figure, or None if required columns missing.
    """
    data = df.copy()
    if "timestamp" in data.columns and ("hour" not in data.columns or "weekday" not in data.columns):
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data["hour"] = data["timestamp"].dt.hour
        data["weekday"] = data["timestamp"].dt.weekday

    if "hour" not in data.columns or "weekday" not in data.columns or "closed_pnl" not in data.columns:
        analytics_logger.warning("Missing 'hour', 'weekday' or 'closed_pnl' for activity heatmap static plot.")
        return None

    if data.empty:
        return None

    # Pivot: hour of day (y) vs weekday (x)
    pivot_df = data.pivot_table(index="hour", columns="weekday", values="closed_pnl", aggfunc="mean")

    # Fill empty slots with 0
    pivot_df = pivot_df.reindex(index=range(24), columns=range(7), fill_value=0.0)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Weekday labels
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    # Render heatmap with diverging green-red palette
    sns.heatmap(
        pivot_df,
        cmap="RdYlGn",
        center=0.0,
        annot=False,  # Numbers might clutter a 24x7 matrix, hover is better or simple colors
        cbar_kws={"label": "Mean PnL (USDT)"},
        xticklabels=days,
        yticklabels=list(range(24)),
        ax=ax,
    )

    ax.set_title(
        "UTC Session Activity Heatmap (Mean PnL)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Day of Week", fontsize=11, labelpad=10)
    ax.set_ylabel("Hour of Day (UTC)", fontsize=11, labelpad=10)

    fig.tight_layout()
    return fig


def plot_hourly_activity_plotly(df: pd.DataFrame) -> Optional[go.Figure]:
    """Generates an interactive heatmap of UTC session activity.

    Args:
        df: Processed DataFrame.

    Returns:
        Optional[go.Figure]: Plotly Figure, or None if required columns missing.
    """
    data = df.copy()
    if "timestamp" in data.columns and ("hour" not in data.columns or "weekday" not in data.columns):
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data["hour"] = data["timestamp"].dt.hour
        data["weekday"] = data["timestamp"].dt.weekday

    if "hour" not in data.columns or "weekday" not in data.columns or "closed_pnl" not in data.columns:
        analytics_logger.warning("Missing 'hour', 'weekday' or 'closed_pnl' for activity heatmap interactive plot.")
        return None

    if data.empty:
        return None

    # Pivot: hour of day (y) vs weekday (x)
    pivot_df = data.pivot_table(index="hour", columns="weekday", values="closed_pnl", aggfunc="mean")
    pivot_df = pivot_df.reindex(index=range(24), columns=range(7), fill_value=0.0)

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_df.to_numpy(),
            x=days,
            y=[f"Hour {h:02d}:00" for h in range(24)],
            colorscale="RdYlGn",
            zmid=0.0,
            hovertemplate="<b>Day:</b> %{x}<br><b>Time:</b> %{y}<br><b>Mean PnL:</b> %{z:.2f} USDT<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="UTC Session Activity Heatmap (Mean PnL)",
            font=dict(size=18, family="Outfit, Inter, sans-serif"),
            x=0.5,
        ),
        xaxis=dict(title="Day of Week"),
        yaxis=dict(
            title="Hour of Day (UTC)",
            autorange="reversed",  # Show Hour 00:00 at the top
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        plot_bgcolor="rgba(30, 41, 59, 1)",
        margin=dict(l=80, r=40, t=60, b=40),
        height=600,
    )
    return fig
