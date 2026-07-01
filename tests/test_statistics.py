"""Test suite for the Phase 5 Statistical Analysis Engine.

Verifies calculation accuracy, hypothesis tests, normality checks, confidence intervals,
effect size estimations, and report outputs under pytest.
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analytics.statistics.confidence_intervals import ConfidenceIntervals
from analytics.statistics.correlation import CorrelationCalculator
from analytics.statistics.descriptive_statistics import DescriptiveStatistics
from analytics.statistics.distribution import DistributionTester
from analytics.statistics.effect_size import EffectSize
from analytics.statistics.hypothesis_testing import HypothesisTester
from analytics.statistics.statistics_engine import StatisticsEngine
from analytics.statistics.summary import StatsSummaryFormatter


@pytest.fixture
def sample_stats_data() -> pd.DataFrame:
    """Generates a sufficiently large sample DataFrame containing processed trading records."""
    # We generate 12 trades to ensure we meet minimum size criteria (e.g. n >= 8 for D'Agostino)
    np.random.seed(42)
    timestamps = pd.date_range(start="2026-06-01 00:00:00", periods=12, freq="12h")

    data = {
        "timestamp": timestamps,
        "entry_timestamp": timestamps,
        "exit_timestamp": timestamps + pd.Timedelta(hours=2),
        "symbol": ["BTCUSDT", "ETHUSDT"] * 6,
        "execution_price": [60000.0, 3000.0, 61000.0, 3100.0] * 3,
        "side": ["BUY", "BUY", "SELL", "SELL"] * 3,
        "size": [0.1, 1.0, 0.2, 0.8] * 3,
        # Closed PnL with custom returns so we have positive/negative variance
        "closed_pnl": [
            10.0,
            -5.0,
            15.0,
            -8.0,
            20.0,
            -12.0,
            2.0,
            0.0,
            30.0,
            -25.0,
            5.0,
            1.0,
        ],
        "account_id": ["BOT-ACC-1", "BOT-ACC-2"] * 6,
        # Alternating fear and greed index values
        "fg_value": [30, 75, 25, 80, 35, 70, 40, 50, 20, 85, 38, 72],
        "fg_classification": [
            "Fear",
            "Greed",
            "Fear",
            "Extreme Greed",
            "Fear",
            "Greed",
            "Fear",
            "Neutral",
            "Extreme Fear",
            "Extreme Greed",
            "Fear",
            "Greed",
        ],
        "fees": [1.5, 0.8, 1.2, 1.0, 1.4, 0.9, 1.1, 0.5, 1.6, 1.1, 1.3, 0.7],
    }
    df = pd.DataFrame(data)
    df["trade_value"] = df["size"] * df["execution_price"]
    df["position_size"] = df["size"]
    df["is_profit"] = (df["closed_pnl"] > 0).astype(int)
    df["profit_percentage"] = (df["closed_pnl"] / df["trade_value"]) * 100.0
    return df


def test_descriptive_statistics(sample_stats_data):
    """Verifies that descriptive statistics are correctly computed."""
    res = DescriptiveStatistics.calculate(sample_stats_data)

    # Check that expected columns are present
    assert "closed_pnl" in res
    assert "fg_value" in res
    assert "size" in res

    # Verify specific calculations for closed_pnl
    pnl_stats = res["closed_pnl"]
    assert pnl_stats["count"] == 12
    assert pnl_stats["min"] == -25.0
    assert pnl_stats["max"] == 30.0
    assert pnl_stats["mean"] == pytest.approx(sample_stats_data["closed_pnl"].mean())
    assert pnl_stats["median"] == pytest.approx(
        sample_stats_data["closed_pnl"].median()
    )
    assert pnl_stats["std_dev"] == pytest.approx(sample_stats_data["closed_pnl"].std())
    assert "quantile_25" in pnl_stats
    assert "quantile_75" in pnl_stats


def test_correlation_calculator(sample_stats_data):
    """Verifies correlation coefficients and p-values are computed."""
    res = CorrelationCalculator.calculate_correlations(sample_stats_data)

    assert "fg_value_vs_closed_pnl" in res
    pnl_corr = res["fg_value_vs_closed_pnl"]

    assert "pearson" in pnl_corr
    assert "spearman" in pnl_corr
    assert "kendall" in pnl_corr
    assert pnl_corr["sample_size"] == 12

    # Verify coefficients are between -1 and 1
    for method in ["pearson", "spearman", "kendall"]:
        coef = pnl_corr[method]["coefficient"]
        p_val = pnl_corr[method]["p_value"]
        assert -1.0 <= coef <= 1.0
        assert 0.0 <= p_val <= 1.0
        assert isinstance(pnl_corr[method]["significant"], bool)


def test_hypothesis_tester(sample_stats_data):
    """Verifies Independent T-Test, Mann-Whitney U, ANOVA, and Chi-Square executions."""
    res = HypothesisTester.run_all_tests(sample_stats_data)

    assert "t_test" in res
    assert "mann_whitney" in res
    assert "anova" in res
    assert "chi_square" in res
    assert "sample_sizes" in res

    # Under this seed, verify outputs exist
    assert res["t_test"]["message"] == "Success"
    assert res["mann_whitney"]["message"] == "Success"
    assert res["anova"]["message"] == "Success"
    assert res["chi_square"]["message"] == "Success"

    assert 0.0 <= res["t_test"]["p_value"] <= 1.0
    assert 0.0 <= res["mann_whitney"]["p_value"] <= 1.0
    assert 0.0 <= res["anova"]["p_value"] <= 1.0
    assert 0.0 <= res["chi_square"]["p_value"] <= 1.0


def test_distribution_tester(sample_stats_data):
    """Verifies normality and two-sample distribution checks."""
    res = DistributionTester.run_tests(sample_stats_data)

    assert "pnl_normality" in res
    assert "fg_normality" in res
    assert "fear_vs_greed_ks_2samp" in res

    # Shapiro-Wilk and KS 1-sample should have run successfully
    assert res["pnl_normality"]["shapiro"]["message"] == "Success"
    assert res["pnl_normality"]["ks_1sample"]["message"] == "Success"

    # Sample size is 12, so D'Agostino normality (requires n >= 8) should pass too
    assert res["pnl_normality"]["dagostino_k2"]["message"] == "Success"

    assert 0.0 <= res["pnl_normality"]["shapiro"]["p_value"] <= 1.0
    assert 0.0 <= res["fear_vs_greed_ks_2samp"]["p_value"] <= 1.0


def test_confidence_intervals(sample_stats_data):
    """Verifies win rate Wilson bounds and Student-t bounds calculations."""
    res = ConfidenceIntervals.calculate(sample_stats_data)

    assert "win_rate" in res
    assert "average_pnl" in res
    assert "average_trade_size" in res

    # Check bounds
    wr = res["win_rate"]
    assert 0.0 <= wr["lower_bound"] <= wr["estimate"] <= wr["upper_bound"] <= 1.0

    ap = res["average_pnl"]
    assert ap["lower_bound"] <= ap["estimate"] <= ap["upper_bound"]


def test_effect_size():
    """Verifies Cohen's d and Eta-squared effect sizes and interpretations."""
    # Group mean differences
    g1 = np.array([10.0, 12.0, 15.0, 11.0, 14.0])
    g2 = np.array([2.0, 4.0, 5.0, 3.0, 6.0])

    d, label_d = EffectSize.cohens_d(g1, g2)
    assert d > 2.0  # Large difference
    assert label_d == "Large"

    # ANOVA group differences
    groups = [g1, g2]
    eta, label_eta = EffectSize.eta_squared(groups)
    assert eta > 0.5
    assert label_eta == "Large"


def test_summary_observations(sample_stats_data):
    """Verifies natural language observations formatter."""
    full_results = {
        "distributions": DistributionTester.run_tests(sample_stats_data),
        "correlations": CorrelationCalculator.calculate_correlations(sample_stats_data),
        "hypothesis_tests": HypothesisTester.run_all_tests(sample_stats_data),
        "confidence_intervals": ConfidenceIntervals.calculate(sample_stats_data),
    }
    observations = StatsSummaryFormatter.generate_observations(full_results)

    assert len(observations) > 0
    # Checks that typical observation segments are generated
    assert any("Normality" in obs for obs in observations) or any(
        "normality" in obs for obs in observations
    )


def test_statistics_engine_execution(sample_stats_data, monkeypatch):
    """Verifies the statistics engine pipeline runs and exports files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Monkeypatch the output directory in config.paths
        import config.paths

        monkeypatch.setattr(config.paths, "ANALYTICS_OUTPUT_DIR", tmp_path)

        # Run orchestrator
        results = StatisticsEngine.run_statistics(
            df=sample_stats_data, export_outputs=True
        )

        assert "descriptive" in results
        assert "correlations" in results
        assert "hypothesis_tests" in results
        assert "distributions" in results
        assert "confidence_intervals" in results
        assert "effect_sizes" in results
        assert "observations" in results

        # Check files exported
        assert (tmp_path / "statistics_summary.json").exists()
        assert (tmp_path / "statistics_summary.csv").exists()
        assert (tmp_path / "hypothesis_results.csv").exists()

        # Check CSV content structure
        hyp_df = pd.read_csv(tmp_path / "hypothesis_results.csv")
        assert len(hyp_df) == 4
        assert "test_name" in hyp_df.columns
        assert "p_value" in hyp_df.columns
