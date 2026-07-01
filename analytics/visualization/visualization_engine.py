"""Visualization Engine orchestrator for PrimeTrade AI.

Integrates static and interactive plotting subsystems to export and index all charts.
"""

from typing import Any, Dict

import pandas as pd

from analytics.visualization.matplotlib_plots import generate_all_static_plots
from analytics.visualization.plotly_dashboard import (
    generate_all_interactive_plots,
    generate_unified_dashboard,
)
from utils.logger import analytics_logger


class VisualizationEngine:
    """Orchestrates visualization generations and file exports for trading data."""

    def __init__(self):
        """Initializes the visualization engine."""
        pass

    def generate_and_save_visualizations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Orchestrates the generation of all static and interactive visualizations.

        Args:
            df: Merged/Processed DataFrame containing trading data and sentiment metrics.

        Returns:
            Dict[str, Any]: Manifest containing paths to all exported chart assets.
        """
        if df is None or df.empty:
            analytics_logger.warning("Empty or None DataFrame passed to VisualizationEngine. No charts generated.")
            return {
                "status": "skipped",
                "message": "Empty DataFrame",
                "static_plots": {},
                "interactive_plots": {},
                "unified_dashboard": None,
            }

        analytics_logger.info(f"Starting visualization suite for {len(df)} records.")

        # 1. Run static matplotlib/seaborn generation
        static_manifest = generate_all_static_plots(df)

        # 2. Run interactive plotly html generation
        interactive_manifest = generate_all_interactive_plots(df)

        # 3. Assemble the unified dashboard
        unified_dashboard_path = generate_unified_dashboard(df)

        manifest = {
            "status": "success",
            "record_count": len(df),
            "static_plots": static_manifest,
            "interactive_plots": interactive_manifest,
            "unified_dashboard": unified_dashboard_path,
        }

        analytics_logger.info("Visualization suite completed successfully.")
        return manifest
