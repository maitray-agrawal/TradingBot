"""Effect size module for PrimeTrade AI.

Calculates Cohen's d (for T-test difference in returns between Fear and Greed)
and Eta-squared (for ANOVA regime return differences).
"""

from typing import List, Optional, Tuple

import numpy as np

from utils.logger import analytics_logger


class EffectSize:
    """Calculates statistical effect sizes to measure the magnitude of differences."""

    @staticmethod
    def cohens_d(group1: np.ndarray, group2: np.ndarray) -> Tuple[Optional[float], str]:
        """Calculates Cohen's d for the difference between two group means.

        Args:
            group1: First group data array.
            group2: Second group data array.

        Returns:
            Tuple[Optional[float], str]: Calculated Cohen's d value (or None) and interpretation tag.
        """
        n1, n2 = len(group1), len(group2)
        if n1 < 2 or n2 < 2:
            return None, "Insufficient sample size (requires n >= 2 per group)"

        mean1, mean2 = np.mean(group1), np.mean(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)

        # Pooled standard deviation
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        if pooled_var <= 0:
            return 0.0, "Negligible"

        pooled_std = np.sqrt(pooled_var)
        d_val = (mean1 - mean2) / pooled_std
        abs_d = abs(d_val)

        # Qualitative interpretation (Cohen 1988)
        if abs_d < 0.2:
            interpretation = "Negligible"
        elif abs_d < 0.5:
            interpretation = "Small"
        elif abs_d < 0.8:
            interpretation = "Medium"
        else:
            interpretation = "Large"

        return float(d_val), interpretation

    @staticmethod
    def eta_squared(groups: List[np.ndarray]) -> Tuple[Optional[float], str]:
        """Calculates Eta-squared (n^2) for One-Way ANOVA across multiple groups.

        Args:
            groups: A list of numpy arrays, one for each group.

        Returns:
            Tuple[Optional[float], str]: Eta-squared value (or None) and interpretation tag.
        """
        # Exclude empty or single-element groups
        active_groups = [g for g in groups if len(g) >= 1]
        k = len(active_groups)
        n_total = sum(len(g) for g in active_groups)

        if k < 2 or n_total < k + 1:
            return (
                None,
                "ANOVA requires at least 2 groups and total samples > number of groups.",
            )

        # Flatten all values to compute global mean
        all_vals = np.concatenate(active_groups)
        global_mean = np.mean(all_vals)

        # SS Total
        ss_total = np.sum((all_vals - global_mean) ** 2)
        if ss_total == 0:
            return 0.0, "Negligible"

        # SS Between (groups)
        ss_between = 0.0
        for g in active_groups:
            n_j = len(g)
            mean_j = np.mean(g)
            ss_between += n_j * ((mean_j - global_mean) ** 2)

        eta_sq = ss_between / ss_total

        # Qualitative interpretation (Cohen 1988)
        # Small: 0.01, Medium: 0.06, Large: 0.14
        if eta_sq < 0.01:
            interpretation = "Negligible"
        elif eta_sq < 0.06:
            interpretation = "Small"
        elif eta_sq < 0.14:
            interpretation = "Medium"
        else:
            interpretation = "Large"

        return float(eta_sq), interpretation
