"""Hypothesis testing module for PrimeTrade AI.

Performs Welch's Independent T-Test, Mann-Whitney U test, One-Way ANOVA,
and Chi-Square test of independence to assess the impact of market sentiment on trading.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from utils.logger import analytics_logger


class HypothesisTester:
    """Performs statistical hypothesis testing on trading performance across sentiment regimes."""

    @staticmethod
    def run_all_tests(df: pd.DataFrame) -> Dict[str, Any]:
        """Runs T-Test, Mann-Whitney U, ANOVA, and Chi-Square tests.

        Args:
            df: DataFrame containing the processed/merged trading data.

        Returns:
            Dict[str, Any]: A dictionary containing statistical test metrics, p-values,
                            and significance determinations.
        """
        analytics_logger.info("Executing hypothesis testing suite...")
        results = {
            "t_test": {
                "stat": None,
                "p_value": None,
                "significant": False,
                "message": "Insufficient data",
            },
            "mann_whitney": {
                "stat": None,
                "p_value": None,
                "significant": False,
                "message": "Insufficient data",
            },
            "anova": {
                "stat": None,
                "p_value": None,
                "significant": False,
                "message": "Insufficient data",
            },
            "chi_square": {
                "stat": None,
                "p_value": None,
                "significant": False,
                "message": "Insufficient data",
            },
        }

        if df.empty:
            analytics_logger.warning("Empty DataFrame provided to HypothesisTester.")
            return results

        # Ensure we have closed_pnl and sentiment data
        if "closed_pnl" not in df.columns:
            analytics_logger.warning("closed_pnl column missing from DataFrame.")
            return results

        # Determine sentiment grouping column
        sentiment_col = None
        if "fg_classification" in df.columns:
            sentiment_col = "fg_classification"
        elif "classification" in df.columns:
            sentiment_col = "classification"

        # If no classification column, create one from fg_value
        df_clean = df.copy()
        if not sentiment_col and "fg_value" in df_clean.columns:
            # Map fg_value to regimes
            def map_regime(val):
                if pd.isna(val):
                    return "Unknown"
                if val < 20:
                    return "Extreme Fear"
                elif val < 45:
                    return "Fear"
                elif val <= 55:
                    return "Neutral"
                elif val <= 80:
                    return "Greed"
                else:
                    return "Extreme Greed"

            df_clean["fg_classification"] = df_clean["fg_value"].apply(map_regime)
            sentiment_col = "fg_classification"

        if not sentiment_col:
            analytics_logger.warning(
                "Sentiment classification columns missing. Hypothesis tests skipped."
            )
            return results

        # Categorize into Fear and Greed groups for two-sample tests
        # Fear: "Fear", "Extreme Fear"
        # Greed: "Greed", "Extreme Greed"
        fear_regimes = ["Fear", "Extreme Fear"]
        greed_regimes = ["Greed", "Extreme Greed"]

        fear_data = df_clean[df_clean[sentiment_col].isin(fear_regimes)][
            "closed_pnl"
        ].dropna()
        greed_data = df_clean[df_clean[sentiment_col].isin(greed_regimes)][
            "closed_pnl"
        ].dropna()

        n_fear = len(fear_data)
        n_greed = len(greed_data)

        results["sample_sizes"] = {
            "fear_group_n": n_fear,
            "greed_group_n": n_greed,
            "total_n": len(df_clean["closed_pnl"].dropna()),
        }

        # 1. Independent T-Test (Welch's T-test, equal_var=False)
        if n_fear >= 2 and n_greed >= 2:
            try:
                # Check for variance in both groups
                if fear_data.var() == 0 and greed_data.var() == 0:
                    results["t_test"] = {
                        "stat": 0.0,
                        "p_value": 1.0,
                        "significant": False,
                        "message": "Zero variance in both groups.",
                    }
                else:
                    t_stat, t_p = stats.ttest_ind(
                        fear_data, greed_data, equal_var=False
                    )
                    results["t_test"] = {
                        "stat": float(t_stat) if not np.isnan(t_stat) else None,
                        "p_value": float(t_p) if not np.isnan(t_p) else None,
                        "significant": bool(t_p < 0.05) if not np.isnan(t_p) else False,
                        "message": "Success",
                    }
            except Exception as e:
                analytics_logger.error(f"Error executing T-test: {e}")
                results["t_test"]["message"] = f"Execution error: {e}"

        # 2. Mann-Whitney U Test (non-parametric two-sample test)
        if n_fear >= 1 and n_greed >= 1:
            try:
                mw_stat, mw_p = stats.mannwhitneyu(
                    fear_data, greed_data, alternative="two-sided"
                )
                results["mann_whitney"] = {
                    "stat": float(mw_stat) if not np.isnan(mw_stat) else None,
                    "p_value": float(mw_p) if not np.isnan(mw_p) else None,
                    "significant": bool(mw_p < 0.05) if not np.isnan(mw_p) else False,
                    "message": "Success",
                }
            except Exception as e:
                analytics_logger.error(f"Error executing Mann-Whitney U: {e}")
                results["mann_whitney"]["message"] = f"Execution error: {e}"

        # 3. One-Way ANOVA (Compare returns across all active sentiment regimes)
        # We group by the classification column and gather closed_pnl lists
        regime_groups = (
            df_clean.groupby(sentiment_col)["closed_pnl"].apply(list).to_dict()
        )
        # Filter groups to only those with >= 2 data points, and exclude Unknown/NaN
        anova_groups = [
            np.array(pnl_list)
            for name, pnl_list in regime_groups.items()
            if name != "Unknown" and len(pnl_list) >= 2
        ]

        if len(anova_groups) >= 2:
            try:
                anova_stat, anova_p = stats.f_oneway(*anova_groups)
                results["anova"] = {
                    "stat": float(anova_stat) if not np.isnan(anova_stat) else None,
                    "p_value": float(anova_p) if not np.isnan(anova_p) else None,
                    "significant": (
                        bool(anova_p < 0.05) if not np.isnan(anova_p) else False
                    ),
                    "message": "Success",
                }
            except Exception as e:
                analytics_logger.error(f"Error executing ANOVA: {e}")
                results["anova"]["message"] = f"Execution error: {e}"
        else:
            results["anova"][
                "message"
            ] = "ANOVA requires at least 2 regimes with at least 2 trade samples each."

        # 4. Chi-Square Test of Independence (regime vs trade outcome [win / loss])
        # Define trade outcome: Win if closed_pnl > 0, Loss if closed_pnl <= 0
        df_clean["outcome"] = np.where(df_clean["closed_pnl"] > 0, "Win", "Loss")

        # Build contingency table
        # We drop 'Unknown' sentiment regimes for the test
        df_chi = df_clean[df_clean[sentiment_col] != "Unknown"]
        if not df_chi.empty:
            contingency_table = pd.crosstab(df_chi[sentiment_col], df_chi["outcome"])

            # Chi-square requirements: table must have at least 2x2 dimensions and non-zero counts
            if contingency_table.shape[0] >= 2 and contingency_table.shape[1] >= 2:
                try:
                    chi2_stat, chi2_p, dof, expected = stats.chi2_contingency(
                        contingency_table
                    )
                    results["chi_square"] = {
                        "stat": float(chi2_stat) if not np.isnan(chi2_stat) else None,
                        "p_value": float(chi2_p) if not np.isnan(chi2_p) else None,
                        "significant": (
                            bool(chi2_p < 0.05) if not np.isnan(chi2_p) else False
                        ),
                        "dof": int(dof),
                        "message": "Success",
                    }
                except Exception as e:
                    analytics_logger.error(f"Error executing Chi-Square test: {e}")
                    results["chi_square"]["message"] = f"Execution error: {e}"
            else:
                results["chi_square"][
                    "message"
                ] = "Chi-Square requires a contingency table of at least 2x2 shape."
        else:
            results["chi_square"][
                "message"
            ] = "No valid data to construct cross-tabulation table."

        analytics_logger.info("Hypothesis testing suite execution complete.")
        return results
