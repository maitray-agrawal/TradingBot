"""Master Strategy Recommendation Engine orchestrator for PrimeTrade AI.

This module loads processed historical trade records, executes registered strategies,
summarizes recommendations, and exports them to JSON, CSV, and Markdown.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from analytics.strategy.base_strategy import BaseStrategy
from analytics.strategy.rule_based import RuleBasedStrategy
from config.paths import PROCESSED_DATA_DIR, STRATEGY_OUTPUT_DIR
from utils.logger import analytics_logger


class StrategyEngine:
    """Orchestrates strategy analysis, aggregates recommendations, and exports results."""

    def __init__(self, strategies: Optional[List[BaseStrategy]] = None):
        """Initializes the Strategy Engine with a list of strategies.

        Args:
            strategies: Optional list of strategies. Defaults to a single RuleBasedStrategy.
        """
        self.strategies: List[BaseStrategy] = strategies or [RuleBasedStrategy()]
        # Ensure output directory exists
        STRATEGY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run_strategy_analysis(
        self,
        df: Optional[pd.DataFrame] = None,
        current_sentiment_val: Optional[float] = None,
        export_outputs: bool = True,
    ) -> Dict[str, Any]:
        """Runs all registered strategies on the dataset and aggregates recommendations.

        Args:
            df: Optional DataFrame of historical preprocessed trades.
                If None, attempts to load from PROCESSED_DATA_DIR.
            current_sentiment_val: Optional latest Fear & Greed Index score.
            export_outputs: Whether to export results to files.

        Returns:
            Dict containing aggregated strategy recommendations.
        """
        analytics_logger.info("Initializing strategy recommendation analysis...")

        # 1. Load data if not provided
        if df is None:
            processed_file = PROCESSED_DATA_DIR / "processed_data.csv"
            if not processed_file.exists():
                analytics_logger.error(
                    f"Processed data file not found at {processed_file}. Cannot run strategy analysis."
                )
                raise FileNotFoundError(
                    f"Missing processed dataset: {processed_file}. Please run the preprocessing or analytics engine first."
                )
            analytics_logger.info(f"Loading processed dataset from {processed_file}...")
            df = pd.read_csv(processed_file)
            # Ensure timestamps are datetime
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])

        # 2. Run each strategy
        recommendations: Dict[str, Any] = {}
        for strategy in self.strategies:
            try:
                analytics_logger.info(f"Executing strategy: {strategy.name}...")
                rec_result = strategy.generate_recommendation(
                    df, current_sentiment_val=current_sentiment_val
                )
                recommendations[strategy.name] = rec_result
            except Exception as e:
                analytics_logger.exception(
                    f"Error executing strategy {strategy.name}: {str(e)}"
                )

        # 3. Export outputs if requested
        if export_outputs and recommendations:
            self._export_results(recommendations)

        return recommendations

    def _export_results(self, recommendations: Dict[str, Any]) -> None:
        """Exports recommendations to JSON, CSV, and Markdown formats.

        Args:
            recommendations: Dictionary of strategy results.
        """
        # Save JSON
        json_path = STRATEGY_OUTPUT_DIR / "recommendations.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(recommendations, f, indent=4, ensure_ascii=False)
        analytics_logger.info(f"Exported JSON recommendations to: {json_path}")

        # Save CSV
        csv_rows = []
        for strat_name, rec in recommendations.items():
            metrics_str = "; ".join([f"{k}={v}" for k, v in rec.get("metrics", {}).items()])
            explanations_str = " | ".join(rec.get("explanations", []))
            csv_rows.append(
                {
                    "strategy_name": strat_name,
                    "action": rec.get("action"),
                    "confidence_score": rec.get("confidence_score"),
                    "explanations": explanations_str,
                    "metrics": metrics_str,
                    "timestamp": rec.get("timestamp"),
                }
            )
        csv_path = STRATEGY_OUTPUT_DIR / "recommendations.csv"
        pd.DataFrame(csv_rows).to_csv(csv_path, index=False)
        analytics_logger.info(f"Exported CSV recommendations to: {csv_path}")

        # Save Markdown
        md_path = STRATEGY_OUTPUT_DIR / "recommendations.md"
        self._write_markdown_report(recommendations, md_path)
        analytics_logger.info(f"Exported Markdown recommendations to: {md_path}")

    def _write_markdown_report(self, recommendations: Dict[str, Any], path: Path) -> None:
        """Writes a beautiful, publication-quality Markdown strategy report.

        Args:
            recommendations: Dictionary of strategy results.
            path: Destination file path.
        """
        lines = [
            "# PrimeTrade AI - Strategy Recommendations",
            "",
            "This report summarizes trading strategy recommendations compiled from account metrics, rolling performance, risk profiles, and market sentiment.",
            "",
            "## Executive Summary Table",
            "",
            "| Strategy Name | Action | Confidence | Timestamp |",
            "| :--- | :---: | :---: | :--- |",
        ]

        for name, rec in recommendations.items():
            action = rec.get("action", "HOLD")
            confidence = rec.get("confidence_score", 0.0)
            timestamp = rec.get("timestamp", "")

            # Apply aesthetic formatting/badges for action
            badge = f"**{action}**"
            if action in ("BUY", "Increase Position Size"):
                badge = f"🟢 **{action}**"
            elif action in ("SELL", "Avoid Trading"):
                badge = f"🔴 **{action}**"
            elif action == "Reduce Leverage":
                badge = f"🟡 **{action}**"

            lines.append(f"| {name} | {badge} | {confidence:.1%} | {timestamp} |")

        lines.extend(["", "## Detailed Strategy Breakdown", ""])

        for name, rec in recommendations.items():
            lines.append(f"### {name}")
            lines.append("")

            # Action Alert block
            action = rec.get("action", "HOLD")
            alert_type = "NOTE"
            if action in ("BUY", "Increase Position Size"):
                alert_type = "TIP"
            elif action == "Reduce Leverage":
                alert_type = "WARNING"
            elif action == "Avoid Trading":
                alert_type = "CAUTION"

            lines.append(f"> [!{alert_type}]")
            lines.append(f"> **Recommended Action:** {action} (Confidence: {rec.get('confidence_score', 0.0):.1%})")

            lines.append("")
            lines.append("**Explanations & Logic:**")
            for exp in rec.get("explanations", []):
                lines.append(f"- {exp}")

            lines.append("")
            lines.append("**Key Computed Metrics:**")
            lines.append("| Metric | Value |")
            lines.append("| :--- | :--- |")
            for k, v in rec.get("metrics", {}).items():
                # Format key for readability
                display_key = k.replace("_", " ").title()
                # Format value
                if isinstance(v, float):
                    if "rate" in k or "drawdown" in k:
                        display_val = f"{v:.2%}"
                    else:
                        display_val = f"{v:.4f}"
                else:
                    display_val = str(v)
                lines.append(f"| {display_key} | {display_val} |")

            lines.append("")
            lines.append("---")
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
