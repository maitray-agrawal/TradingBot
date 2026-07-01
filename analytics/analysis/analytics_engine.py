"""Master analytics engine orchestration module for PrimeTrade AI.

Loads or preprocesses the dataset, invokes the various sub-analysis calculators
(trader, market, sentiment, coin, performance, risk, time, correlation),
compiles intelligence summaries, and exports results to JSON, CSV, and Markdown formats.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from analytics.analysis.coin_analysis import CoinAnalysis
from analytics.analysis.correlation_analysis import CorrelationAnalysis
from analytics.analysis.market_analysis import MarketAnalysis
from analytics.analysis.performance_analysis import PerformanceAnalysis
from analytics.analysis.risk_analysis import RiskAnalysis
from analytics.analysis.sentiment_analysis import SentimentAnalysis
from analytics.analysis.summary_generator import SummaryGenerator
from analytics.analysis.time_analysis import TimeAnalysis
from analytics.analysis.trader_analysis import TraderAnalysis
from analytics.feature_engineering.generator import FeatureGenerator
from analytics.preprocessing.merger import DatasetMerger
from analytics.preprocessing.normalizer import DataNormalizer
from config.paths import ANALYTICS_OUTPUT_DIR, DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR, UPLOADS_DATA_DIR
from utils.logger import analytics_logger


class AnalyticsEngine:
    """The entry point for generating complete system-wide trading intelligence."""

    @classmethod
    def _run_preprocessing_pipeline(cls) -> pd.DataFrame:
        """Private helper to preprocess raw/mock data if processed file does not exist."""
        analytics_logger.info("Processed dataset missing. Executing preprocessing pipeline fallback...")

        # Resolve paths
        trader_path: Optional[Path] = None
        fg_path: Optional[Path] = None

        # 1. Look for live/uploaded datasets
        live_trader = RAW_DATA_DIR / "binance_futures_trades.csv"
        live_fg = UPLOADS_DATA_DIR / "fear_greed_index.xlsx"

        if live_trader.exists():
            trader_path = live_trader
        elif (DATA_DIR / "mock_trader_history.xlsx").exists():
            trader_path = DATA_DIR / "mock_trader_history.xlsx"

        if live_fg.exists():
            fg_path = live_fg
        elif (DATA_DIR / "mock_fear_greed_index.csv").exists():
            fg_path = DATA_DIR / "mock_fear_greed_index.csv"

        if not trader_path or not fg_path:
            raise FileNotFoundError(f"Cannot run preprocessing fallback: raw/mock files missing from {DATA_DIR}.")

        # 2. Run cleansing
        normalizer = DataNormalizer()
        analytics_logger.info(f"Cleaning trader data from: {trader_path.name}")
        trader_clean, _ = normalizer.clean_trader_data(trader_path)

        analytics_logger.info(f"Cleaning Fear & Greed data from: {fg_path.name}")
        fg_clean, _ = normalizer.clean_fear_greed_data(fg_path)

        # 3. Feature engineering
        analytics_logger.info("Generating features...")
        featured_trader = FeatureGenerator.generate_features(trader_clean)

        # 4. Merge datasets
        analytics_logger.info("Merging datasets...")
        merged_df = DatasetMerger.merge_datasets(featured_trader, fg_clean, strategy="nearest")

        # 5. Write to processed
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        processed_file_path = PROCESSED_DATA_DIR / "processed_data.csv"
        merged_df.to_csv(processed_file_path, index=False)
        analytics_logger.info(f"Processed dataset saved to: {processed_file_path}")

        return merged_df

    @classmethod
    def run_analysis(
        cls,
        df: Optional[pd.DataFrame] = None,
        processed_path: Optional[str] = None,
        export_outputs: bool = True,
    ) -> Dict[str, Any]:
        """Runs the entire suite of analytics on the trading history dataset.

        Args:
            df: Optional preloaded pandas DataFrame. If not provided, loads from path.
            processed_path: Optional path to processed dataset (defaults to standard processed dir).
            export_outputs: Whether to export results to the analytics/outputs directory.

        Returns:
            Dict[str, Any]: All compiled metrics and textual summaries.
        """
        analytics_logger.info("Starting master analytics engine run...")

        # 1. Load or Preprocess Dataset
        if df is None:
            p_path = Path(processed_path) if processed_path else (PROCESSED_DATA_DIR / "processed_data.csv")
            if not p_path.exists() or p_path.stat().st_size == 0:
                df = cls._run_preprocessing_pipeline()
            else:
                analytics_logger.info(f"Loading processed dataset from {p_path}")
                df = pd.read_csv(p_path)

        # 2. Trigger Sub-Analyses
        trader_res = TraderAnalysis.calculate_metrics(df)
        market_res = MarketAnalysis.calculate_metrics(df)
        sentiment_res = SentimentAnalysis.calculate_metrics(df)
        coin_res = CoinAnalysis.calculate_metrics(df)
        performance_res = PerformanceAnalysis.calculate_metrics(df)
        risk_res = RiskAnalysis.calculate_metrics(df)
        time_res = TimeAnalysis.calculate_metrics(df)
        correlation_res = CorrelationAnalysis.calculate_metrics(df)

        # 3. Generate Executive Summary and Intelligence Highlights
        summary_res = SummaryGenerator.generate_summary(
            trader_results=trader_res,
            market_results=market_res,
            sentiment_results=sentiment_res,
            coin_results=coin_res,
            performance_results=performance_res,
            risk_results=risk_res,
            time_results=time_res,
            correlation_results=correlation_res,
        )

        # 4. Compile into global payload
        full_results = {
            "trader_analysis": asdict(trader_res),
            "market_analysis": asdict(market_res),
            "sentiment_analysis": asdict(sentiment_res),
            "coin_analysis": asdict(coin_res),
            "performance_analysis": asdict(performance_res),
            "risk_analysis": asdict(risk_res),
            "time_analysis": asdict(time_res),
            "correlation_analysis": asdict(correlation_res),
            "intelligence_summary": summary_res,
        }

        # 5. Export Results if requested
        if export_outputs:
            cls.export_results(full_results)

        analytics_logger.info("Master analytics run completed successfully.")
        return full_results

    @classmethod
    def export_results(cls, results: Dict[str, Any]) -> None:
        """Exports calculation results to files in the analytics outputs folder."""
        ANALYTICS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        analytics_logger.info(f"Exporting analytics results to: {ANALYTICS_OUTPUT_DIR}")

        # A. JSON summary export
        json_path = ANALYTICS_OUTPUT_DIR / "analytics_summary.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=4, default=str)
        analytics_logger.info(f"Saved JSON summary: {json_path.name}")

        # B. Flattened CSV summary export
        # Creates a single-row CSV containing global scalars
        scalar_dict = {
            "total_trades": results["performance_analysis"]["total_trades"],
            "net_profit": results["performance_analysis"]["net_profit"],
            "win_rate": results["performance_analysis"]["win_rate"],
            "loss_rate": results["performance_analysis"]["loss_rate"],
            "profit_factor": results["performance_analysis"]["profit_factor"],
            "average_trade_size": results["performance_analysis"]["average_trade_size"],
            "max_drawdown": results["risk_analysis"]["max_drawdown"],
            "value_at_risk_95": results["risk_analysis"]["value_at_risk_95"],
            "expected_shortfall_95": results["risk_analysis"]["expected_shortfall_95"],
            "composite_risk_score": results["risk_analysis"]["composite_risk_score"],
            "total_traders": results["trader_analysis"]["total_traders"],
            "best_performing_coin": results["coin_analysis"]["best_performing_coin"],
            "worst_performing_coin": results["coin_analysis"]["worst_performing_coin"],
        }
        csv_summary_path = ANALYTICS_OUTPUT_DIR / "analytics_summary.csv"
        pd.DataFrame([scalar_dict]).to_csv(csv_summary_path, index=False)
        analytics_logger.info(f"Saved CSV summary: {csv_summary_path.name}")

        # C. Leaderboards CSV export
        # Compiles trader PnLs and Coin PnLs side-by-side or stacked
        traders_list = results["trader_analysis"]["top_10_traders"]
        coins_list = results["coin_analysis"]["ranked_coins_list"]

        traders_df = pd.DataFrame(traders_list)[["account_id", "total_pnl", "win_rate", "trade_count"]]
        coins_df = pd.DataFrame(coins_list)[["symbol", "total_pnl", "win_rate", "trade_count"]]

        leaderboard_path = ANALYTICS_OUTPUT_DIR / "leaderboards.csv"
        # We save them in a clean stacked CSV or write separate files, stacked is nice:
        with open(leaderboard_path, "w") as f:
            f.write("=== TRADER LEADERBOARD ===\n")
            traders_df.to_csv(f, index=False)
            f.write("\n=== COIN PERFORMANCE RANKINGS ===\n")
            coins_df.to_csv(f, index=False)
        analytics_logger.info(f"Saved Leaderboards: {leaderboard_path.name}")

        # D. Risk metrics CSV export
        risk_dict = results["risk_analysis"]
        # Filter to remove dict/list components if any, keeping keys
        flat_risk = {k: v for k, v in risk_dict.items() if not isinstance(v, (dict, list))}
        risk_csv_path = ANALYTICS_OUTPUT_DIR / "risk_metrics.csv"
        pd.DataFrame([flat_risk]).to_csv(risk_csv_path, index=False)
        analytics_logger.info(f"Saved Risk Metrics: {risk_csv_path.name}")

        # E. Executive Summary Markdown report export
        intel = results["intelligence_summary"]
        report_path = ANALYTICS_OUTPUT_DIR / "executive_summary.md"

        md_content = f"""# PrimeTrade AI - Executive Analytics & Risk Report
Generated on: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S UTC")}

## 1. Executive Summary
{intel["executive_summary"]}

## 2. Key Trading Metrics
- **Total Trades**: {results["performance_analysis"]["total_trades"]}
- **Winning / Losing Trades**: {results["performance_analysis"]["winning_trades"]} / {results["performance_analysis"]["losing_trades"]}
- **Win Rate**: {results["performance_analysis"]["win_rate"] * 100.0:.2f}%
- **Profit Factor**: {results["performance_analysis"]["profit_factor"]:.2f}
- **Net Realized PnL**: ${results["performance_analysis"]["net_profit"]:,.2f}
- **Gross Profit / Loss**: ${results["performance_analysis"]["gross_profit"]:,.2f} / ${results["performance_analysis"]["gross_loss"]:,.2f}
- **Maximum Drawdown**: ${results["risk_analysis"]["max_drawdown"]:,.2f}

## 3. High-Value Intelligence Insights
### Top Insights
"""
        for ins in intel["top_insights"]:
            md_content += f"- {ins}\n"

        md_content += "\n### Important Observations\n"
        for obs in intel["important_observations"]:
            md_content += f"- {obs}\n"

        md_content += "\n## 4. Strategic Business Recommendations\n"
        for rec in intel["business_recommendations"]:
            md_content += f"- {rec}\n"

        md_content += "\n## 5. Systemic Risk Warnings\n"
        for warn in intel["risk_warnings"]:
            md_content += f"- {warn}\n"

        with open(report_path, "w") as f:
            f.write(md_content)
        analytics_logger.info(f"Saved Markdown Executive Summary: {report_path.name}")
