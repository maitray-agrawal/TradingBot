"""Master statistical analysis engine coordinator for PrimeTrade AI.

Loads or preprocesses the dataset, executes descriptive statistics, correlations,
hypothesis testing, distributions, confidence intervals, and effect sizes, and exports
results to JSON and CSV summaries.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

import config.paths
from analytics.feature_engineering.generator import FeatureGenerator
from analytics.preprocessing.merger import DatasetMerger
from analytics.preprocessing.normalizer import DataNormalizer
from analytics.statistics.confidence_intervals import ConfidenceIntervals
from analytics.statistics.correlation import CorrelationCalculator
from analytics.statistics.descriptive_statistics import DescriptiveStatistics
from analytics.statistics.distribution import DistributionTester
from analytics.statistics.effect_size import EffectSize
from analytics.statistics.hypothesis_testing import HypothesisTester
from analytics.statistics.summary import StatsSummaryFormatter
from utils.logger import analytics_logger


class StatisticsEngine:
    """Orchestrates all statistical computations, hypothesis tests, and summary exports."""

    @classmethod
    def _run_preprocessing_pipeline(cls) -> pd.DataFrame:
        """Private helper to preprocess raw/mock data if processed file does not exist."""
        analytics_logger.info("Processed dataset missing. Executing preprocessing pipeline fallback...")

        # Resolve paths
        trader_path: Optional[Path] = None
        fg_path: Optional[Path] = None

        # Look for live/uploaded datasets
        live_trader = config.paths.RAW_DATA_DIR / "binance_futures_trades.csv"
        live_fg = config.paths.UPLOADS_DATA_DIR / "fear_greed_index.xlsx"

        if live_trader.exists():
            trader_path = live_trader
        elif (config.paths.DATA_DIR / "mock_trader_history.xlsx").exists():
            trader_path = config.paths.DATA_DIR / "mock_trader_history.xlsx"

        if live_fg.exists():
            fg_path = live_fg
        elif (config.paths.DATA_DIR / "mock_fear_greed_index.csv").exists():
            fg_path = config.paths.DATA_DIR / "mock_fear_greed_index.csv"

        if not trader_path or not fg_path:
            raise FileNotFoundError(f"Cannot run preprocessing fallback: raw/mock files missing from {config.paths.DATA_DIR}.")

        # Run cleansing
        normalizer = DataNormalizer()
        trader_clean, _ = normalizer.clean_trader_data(trader_path)
        fg_clean, _ = normalizer.clean_fear_greed_data(fg_path)

        # Feature engineering
        featured_trader = FeatureGenerator.generate_features(trader_clean)

        # Merge datasets
        merged_df = DatasetMerger.merge_datasets(featured_trader, fg_clean, strategy="nearest")

        # Save to processed
        config.paths.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        processed_file_path = config.paths.PROCESSED_DATA_DIR / "processed_data.csv"
        merged_df.to_csv(processed_file_path, index=False)
        analytics_logger.info(f"Processed dataset saved to: {processed_file_path}")

        return merged_df

    @classmethod
    def run_statistics(
        cls,
        df: Optional[pd.DataFrame] = None,
        processed_path: Optional[str] = None,
        export_outputs: bool = True,
    ) -> Dict[str, Any]:
        """Runs the entire suite of statistical tests and exports report data.

        Args:
            df: Optional pre-loaded DataFrame.
            processed_path: Optional path to processed dataset.
            export_outputs: Whether to write outputs to analytics/outputs/.

        Returns:
            Dict[str, Any]: Nest payload containing descriptive statistics, correlations,
                            hypothesis testing, distributions, confidence intervals, effect sizes,
                            and observations.
        """
        analytics_logger.info("Initializing statistical analysis pipeline...")

        # 1. Load or Preprocess Dataset
        if df is None:
            p_path = Path(processed_path) if processed_path else (config.paths.PROCESSED_DATA_DIR / "processed_data.csv")
            if not p_path.exists() or p_path.stat().st_size == 0:
                df = cls._run_preprocessing_pipeline()
            else:
                analytics_logger.info(f"Loading processed dataset from {p_path}")
                df = pd.read_csv(p_path)

        # 2. Compute components
        descriptive_res = DescriptiveStatistics.calculate(df)
        correlation_res = CorrelationCalculator.calculate_correlations(df)
        hypothesis_res = HypothesisTester.run_all_tests(df)
        distribution_res = DistributionTester.run_tests(df)
        ci_res = ConfidenceIntervals.calculate(df)

        # 3. Calculate effect sizes
        cohen_val, cohen_label = None, "N/A"
        eta_val, eta_label = None, "N/A"

        # Determine sentiment column for grouping
        sentiment_col = (
            "fg_classification"
            if "fg_classification" in df.columns
            else ("classification" if "classification" in df.columns else None)
        )
        if not sentiment_col and "fg_value" in df.columns:
            df_temp = df.copy()
            df_temp["fg_classification"] = df_temp["fg_value"].apply(
                lambda val: "Fear" if val < 45 else ("Greed" if val > 55 else "Neutral")
            )
            df = df_temp
            sentiment_col = "fg_classification"

        if sentiment_col and "closed_pnl" in df.columns:
            # Cohen's d (Fear vs Greed PnL)
            fear_pnl = df[df[sentiment_col].isin(["Fear", "Extreme Fear"])]["closed_pnl"].dropna().to_numpy()
            greed_pnl = df[df[sentiment_col].isin(["Greed", "Extreme Greed"])]["closed_pnl"].dropna().to_numpy()
            cohen_val, cohen_label = EffectSize.cohens_d(fear_pnl, greed_pnl)

            # Eta-squared (ANOVA regimes)
            grouped = df.groupby(sentiment_col)["closed_pnl"].apply(lambda s: s.dropna().to_numpy()).to_dict()
            anova_groups = [arr for name, arr in grouped.items() if name != "Unknown" and len(arr) >= 2]
            eta_val, eta_label = EffectSize.eta_squared(anova_groups)

        effect_sizes = {
            "cohens_d": {
                "value": cohen_val,
                "interpretation": cohen_label,
            },
            "eta_squared": {
                "value": eta_val,
                "interpretation": eta_label,
            },
        }

        # 4. Compile into structured payload
        full_results = {
            "descriptive": descriptive_res,
            "correlations": correlation_res,
            "hypothesis_tests": hypothesis_res,
            "distributions": distribution_res,
            "confidence_intervals": ci_res,
            "effect_sizes": effect_sizes,
        }

        # Generate text observations
        observations = StatsSummaryFormatter.generate_observations(full_results)
        full_results["observations"] = observations

        # 5. Export outputs
        if export_outputs:
            cls.export_results(full_results)

        analytics_logger.info("Statistical analysis run completed successfully.")
        return full_results

    @classmethod
    def export_results(cls, results: Dict[str, Any]) -> None:
        """Exports statistical summaries and hypothesis results to output directories."""
        config.paths.ANALYTICS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        analytics_logger.info(f"Exporting statistical results to: {config.paths.ANALYTICS_OUTPUT_DIR}")

        # A. JSON summary export
        json_path = config.paths.ANALYTICS_OUTPUT_DIR / "statistics_summary.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=4, default=str)
        analytics_logger.info(f"Saved statistics JSON summary: {json_path.name}")

        # B. Flattened CSV summary export
        # Extract key scalars for high-level parsing
        win_rate_ci = results.get("confidence_intervals", {}).get("win_rate", {})
        pnl_ci = results.get("confidence_intervals", {}).get("average_pnl", {})
        pnl_corr = results.get("correlations", {}).get("fg_value_vs_closed_pnl", {})
        t_test = results.get("hypothesis_tests", {}).get("t_test", {})
        anova = results.get("hypothesis_tests", {}).get("anova", {})
        chi = results.get("hypothesis_tests", {}).get("chi_square", {})

        scalar_dict = {
            "win_rate_estimate": win_rate_ci.get("estimate"),
            "win_rate_ci_lower": win_rate_ci.get("lower_bound"),
            "win_rate_ci_upper": win_rate_ci.get("upper_bound"),
            "mean_pnl_estimate": pnl_ci.get("estimate"),
            "mean_pnl_ci_lower": pnl_ci.get("lower_bound"),
            "mean_pnl_ci_upper": pnl_ci.get("upper_bound"),
            "pearson_coef_fg_vs_pnl": pnl_corr.get("pearson", {}).get("coefficient"),
            "pearson_p_fg_vs_pnl": pnl_corr.get("pearson", {}).get("p_value"),
            "pearson_significant_fg_vs_pnl": pnl_corr.get("pearson", {}).get("significant"),
            "spearman_coef_fg_vs_pnl": pnl_corr.get("spearman", {}).get("coefficient"),
            "spearman_p_fg_vs_pnl": pnl_corr.get("spearman", {}).get("p_value"),
            "t_test_stat": t_test.get("stat"),
            "t_test_p": t_test.get("p_value"),
            "t_test_significant": t_test.get("significant"),
            "cohens_d": results.get("effect_sizes", {}).get("cohens_d", {}).get("value"),
            "cohens_d_interpretation": results.get("effect_sizes", {}).get("cohens_d", {}).get("interpretation"),
            "anova_stat": anova.get("stat"),
            "anova_p": anova.get("p_value"),
            "anova_significant": anova.get("significant"),
            "eta_squared": results.get("effect_sizes", {}).get("eta_squared", {}).get("value"),
            "eta_squared_interpretation": results.get("effect_sizes", {}).get("eta_squared", {}).get("interpretation"),
            "chi_square_stat": chi.get("stat"),
            "chi_square_p": chi.get("p_value"),
            "chi_square_significant": chi.get("significant"),
        }

        csv_summary_path = config.paths.ANALYTICS_OUTPUT_DIR / "statistics_summary.csv"
        pd.DataFrame([scalar_dict]).to_csv(csv_summary_path, index=False)
        analytics_logger.info(f"Saved statistics CSV summary: {csv_summary_path.name}")

        # C. Hypothesis results tabular CSV export
        hypothesis_rows = []

        # T-Test row
        t_sig = StatsSummaryFormatter.interpret_p_value(t_test.get("p_value"))
        hypothesis_rows.append(
            {
                "test_name": "Independent T-Test (Fear vs Greed Returns)",
                "test_statistic": t_test.get("stat"),
                "p_value": t_test.get("p_value"),
                "is_significant": t_test.get("significant"),
                "interpretation": t_sig,
                "effect_size_value": results.get("effect_sizes", {}).get("cohens_d", {}).get("value"),
                "effect_size_interpretation": results.get("effect_sizes", {}).get("cohens_d", {}).get("interpretation"),
            }
        )

        # Mann-Whitney U row
        mw = results.get("hypothesis_tests", {}).get("mann_whitney", {})
        mw_sig = StatsSummaryFormatter.interpret_p_value(mw.get("p_value"))
        hypothesis_rows.append(
            {
                "test_name": "Mann-Whitney U Test (Fear vs Greed Distributions)",
                "test_statistic": mw.get("stat"),
                "p_value": mw.get("p_value"),
                "is_significant": mw.get("significant"),
                "interpretation": mw_sig,
                "effect_size_value": None,
                "effect_size_interpretation": "N/A",
            }
        )

        # ANOVA row
        anova_sig = StatsSummaryFormatter.interpret_p_value(anova.get("p_value"))
        hypothesis_rows.append(
            {
                "test_name": "One-Way ANOVA (Returns Across Regimes)",
                "test_statistic": anova.get("stat"),
                "p_value": anova.get("p_value"),
                "is_significant": anova.get("significant"),
                "interpretation": anova_sig,
                "effect_size_value": results.get("effect_sizes", {}).get("eta_squared", {}).get("value"),
                "effect_size_interpretation": results.get("effect_sizes", {}).get("eta_squared", {}).get("interpretation"),
            }
        )

        # Chi-Square row
        chi_sig = StatsSummaryFormatter.interpret_p_value(chi.get("p_value"))
        hypothesis_rows.append(
            {
                "test_name": "Chi-Square Test of Independence (Regime vs Outcome)",
                "test_statistic": chi.get("stat"),
                "p_value": chi.get("p_value"),
                "is_significant": chi.get("significant"),
                "interpretation": chi_sig,
                "effect_size_value": None,
                "effect_size_interpretation": "N/A",
            }
        )

        hypothesis_df = pd.DataFrame(hypothesis_rows)
        hypothesis_csv_path = config.paths.ANALYTICS_OUTPUT_DIR / "hypothesis_results.csv"
        hypothesis_df.to_csv(hypothesis_csv_path, index=False)
        analytics_logger.info(f"Saved hypothesis results CSV: {hypothesis_csv_path.name}")
