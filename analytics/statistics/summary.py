"""Statistical summary and formatter module for PrimeTrade AI.

Interprets the outputs of hypothesis tests, distribution checks, and correlations,
generating natural language conclusions and formatting reports.
"""

from typing import Any, Dict, List

import pandas as pd


class StatsSummaryFormatter:
    """Formats and interprets raw statistical results into structured insights."""

    @staticmethod
    def interpret_p_value(p_val: Any, alpha: float = 0.05) -> str:
        """Helper to interpret a p-value with respect to alpha."""
        if p_val is None or pd.isna(p_val):
            return "Indeterminate (Insufficient Data)"

        p = float(p_val)
        if p < 0.001:
            return f"Highly Significant (p < 0.001, alpha={alpha})"
        elif p < alpha:
            return f"Statistically Significant (p={p:.4f}, alpha={alpha})"
        else:
            return f"Not Statistically Significant (p={p:.4f}, alpha={alpha})"

    @staticmethod
    def generate_observations(stats_data: Dict[str, Any]) -> List[str]:
        """Translates computed statistical values into textual observations.

        Args:
            stats_data: Aggregate statistical payload containing results of all tests.

        Returns:
            List[str]: Formatted observations.
        """
        observations = []
        alpha = 0.05

        # 1. Normality Observations
        pnl_norm = stats_data.get("distributions", {}).get("pnl_normality", {})
        shapiro_pnl = pnl_norm.get("shapiro", {}).get("p_value")
        if shapiro_pnl is not None:
            is_normal = pnl_norm.get("shapiro", {}).get("normal", False)
            status = (
                "follows a normal distribution"
                if is_normal
                else "does NOT follow a normal distribution"
            )
            observations.append(
                f"Normality Test: Shapiro-Wilk test indicates that trade PnL returns {status} "
                f"(p-value: {shapiro_pnl:.5f})."
            )

        # 2. Fear vs Greed correlation
        corr_data = stats_data.get("correlations", {})
        pnl_corr = corr_data.get("fg_value_vs_closed_pnl", {})
        pearson_coef = pnl_corr.get("pearson", {}).get("coefficient")
        spearman_coef = pnl_corr.get("spearman", {}).get("coefficient")
        pearson_p = pnl_corr.get("pearson", {}).get("p_value")

        if pearson_coef is not None:
            sig_text = (
                "significant"
                if pnl_corr.get("pearson", {}).get("significant")
                else "non-significant"
            )
            dir_text = "positive" if pearson_coef > 0 else "negative"
            strength = (
                "weak"
                if abs(pearson_coef) < 0.3
                else ("moderate" if abs(pearson_coef) < 0.6 else "strong")
            )
            observations.append(
                f"Correlation Analysis: Fear & Greed index vs closed PnL has a {sig_text}, {strength} {dir_text} "
                f"linear relationship (Pearson r: {pearson_coef:.4f}, p-value: {pearson_p:.5f})."
            )

        # 3. Two-sample Hypothesis tests
        ht_data = stats_data.get("hypothesis_tests", {})
        t_test = ht_data.get("t_test", {})
        mw_test = ht_data.get("mann_whitney", {})

        t_p = t_test.get("p_value")
        if t_p is not None and t_test.get("message") == "Success":
            sig_status = (
                "significant difference"
                if t_test.get("significant")
                else "no significant difference"
            )
            observations.append(
                f"Welch's T-Test: Compares average closed PnL between Fear and Greed regimes. "
                f"Results show {sig_status} in average performance (T-stat: {t_test.get('stat'):.4f}, p-value: {t_p:.5f})."
            )

        mw_p = mw_test.get("p_value")
        if mw_p is not None and mw_test.get("message") == "Success":
            sig_status = (
                "significant difference"
                if mw_test.get("significant")
                else "no significant difference"
            )
            observations.append(
                f"Mann-Whitney U Test: Compares return distributions between Fear and Greed regimes. "
                f"Results show {sig_status} (U-stat: {mw_test.get('stat'):.1f}, p-value: {mw_p:.5f})."
            )

        # 4. ANOVA
        anova = ht_data.get("anova", {})
        anova_p = anova.get("p_value")
        if anova_p is not None and anova.get("message") == "Success":
            sig_status = (
                "significant difference"
                if anova.get("significant")
                else "no significant difference"
            )
            observations.append(
                f"One-Way ANOVA: Evaluates performance across all active sentiment regimes. "
                f"Indicates {sig_status} in mean returns across groups (F-stat: {anova.get('stat'):.4f}, p-value: {anova_p:.5f})."
            )

        # 5. Chi-Square
        chi = ht_data.get("chi_square", {})
        chi_p = chi.get("p_value")
        if chi_p is not None and chi.get("message") == "Success":
            sig_status = "dependent on" if chi.get("significant") else "independent of"
            observations.append(
                f"Chi-Square Test: Trade outcome (Win/Loss) counts are statistically {sig_status} the "
                f"sentiment regimes (Chi2-stat: {chi.get('stat'):.4f}, p-value: {chi_p:.5f}, DOF: {chi.get('dof')})."
            )

        # Fallback if no observations generated
        if not observations:
            observations.append(
                "Insufficient data collected to formulate statistical observations."
            )

        return observations
