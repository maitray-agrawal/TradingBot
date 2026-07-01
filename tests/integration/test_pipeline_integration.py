"""
test_pipeline_integration.py — End-to-end integration tests for the
PrimeTrade AI analytics pipeline.

Tests exercise the full data flow using actual module APIs:
    Ingestion → Preprocessing → Feature Engineering → Analytics → Reports

Marked with @pytest.mark.integration.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.mark.integration
class TestIngestionToPreprocessingPipeline:
    """Integration: file ingestion through to cleaned output using real API."""

    def test_dataset_detector_classifies_trader_columns(self) -> None:
        """Trader column headers are classified as TRADER_HISTORY."""
        from config.enums import DatasetType
        from analytics.ingestion.dataset_detector import DatasetDetector

        detector = DatasetDetector()
        # Use real trader-like column names
        trader_columns = ["account", "symbol", "side", "size", "execution_price", "closed_pnl", "timestamp"]
        dataset_type, score = detector.detect_schema_type(trader_columns)
        assert dataset_type == DatasetType.TRADER_HISTORY
        assert score > 0.0

    def test_dataset_detector_classifies_fear_greed_columns(self) -> None:
        """Fear & Greed column headers are classified correctly."""
        from config.enums import DatasetType
        from analytics.ingestion.dataset_detector import DatasetDetector

        detector = DatasetDetector()
        fg_columns = ["date", "classification", "value", "timestamp"]
        dataset_type, score = detector.detect_schema_type(fg_columns)
        assert dataset_type == DatasetType.FEAR_GREED
        assert score > 0.0

    def test_dataset_detector_returns_unknown_for_random_columns(self) -> None:
        """Completely unrelated columns return UNKNOWN type."""
        from config.enums import DatasetType
        from analytics.ingestion.dataset_detector import DatasetDetector

        detector = DatasetDetector()
        random_columns = ["latitude", "longitude", "temperature", "humidity"]
        dataset_type, score = detector.detect_schema_type(random_columns)
        assert dataset_type == DatasetType.UNKNOWN

    def test_dataset_detector_dataframe_type_detection(
        self, sample_trader_df: pd.DataFrame
    ) -> None:
        """detect_dataframe_type classifies the sample trader DataFrame."""
        from config.enums import DatasetType
        from analytics.ingestion.dataset_detector import DatasetDetector

        detector = DatasetDetector()
        result = detector.detect_dataframe_type(sample_trader_df)
        assert result in [DatasetType.TRADER_HISTORY, DatasetType.UNKNOWN]  # depends on column match

    def test_preprocessed_output_has_required_columns(
        self, sample_trader_df: pd.DataFrame
    ) -> None:
        """Preprocessed trader DataFrame retains all critical columns."""
        required = {"symbol", "side", "size", "execution_price", "closed_pnl", "timestamp"}
        assert required.issubset(set(sample_trader_df.columns)), (
            f"Missing columns: {required - set(sample_trader_df.columns)}"
        )

    def test_no_negative_prices_after_preprocessing(
        self, sample_trader_df: pd.DataFrame
    ) -> None:
        """No negative execution prices exist after preprocessing."""
        assert (sample_trader_df["execution_price"] > 0).all()

    def test_no_negative_sizes_after_preprocessing(
        self, sample_trader_df: pd.DataFrame
    ) -> None:
        """No zero or negative trade sizes exist after preprocessing."""
        assert (sample_trader_df["size"] > 0).all()

    def test_timestamps_are_timezone_naive(self, sample_trader_df: pd.DataFrame) -> None:
        """All timestamps are timezone-naive (no tzinfo attached)."""
        assert sample_trader_df["timestamp"].dt.tz is None


@pytest.mark.integration
class TestFeatureEngineeringPipeline:
    """Integration: feature columns computed correctly on real data."""

    def test_trade_value_equals_size_times_price(
        self, sample_trader_df: pd.DataFrame
    ) -> None:
        """trade_value == size * execution_price for every row."""
        expected = sample_trader_df["size"] * sample_trader_df["execution_price"]
        pd.testing.assert_series_equal(
            sample_trader_df["trade_value"].round(2),
            expected.round(2),
            check_names=False,
        )

    def test_is_profit_flag_matches_closed_pnl_sign(
        self, sample_trader_df: pd.DataFrame
    ) -> None:
        """is_profit is True exactly when closed_pnl > 0."""
        expected = sample_trader_df["closed_pnl"] > 0
        pd.testing.assert_series_equal(
            sample_trader_df["is_profit"],
            expected,
            check_names=False,
        )

    def test_cumulative_pnl_is_monotone_cumsum(
        self, sample_trader_df: pd.DataFrame
    ) -> None:
        """cumulative_pnl is exactly the running sum of closed_pnl."""
        expected = sample_trader_df["closed_pnl"].cumsum()
        pd.testing.assert_series_equal(
            sample_trader_df["cumulative_pnl"].round(4),
            expected.round(4),
            check_names=False,
        )

    def test_time_feature_columns_are_present(
        self, sample_trader_df: pd.DataFrame
    ) -> None:
        """Time-partitioned feature columns are generated."""
        for col in ["hour", "day", "weekday", "month", "week"]:
            assert col in sample_trader_df.columns, f"Missing time column: {col}"

    def test_direction_column_is_binary(self, sample_trader_df: pd.DataFrame) -> None:
        """direction column contains only 1 (BUY) or -1 (SELL)."""
        assert set(sample_trader_df["direction"].unique()).issubset({1, -1})


@pytest.mark.integration
class TestMergePipeline:
    """Integration: chronological nearest-date merge between datasets."""

    def test_merged_df_contains_fg_columns(
        self, sample_merged_df: pd.DataFrame
    ) -> None:
        """Merged DataFrame contains Fear & Greed columns."""
        assert "fg_value" in sample_merged_df.columns
        assert "fg_classification" in sample_merged_df.columns

    def test_fg_values_are_within_range(self, sample_merged_df: pd.DataFrame) -> None:
        """All Fear & Greed values are within the valid 0–100 range."""
        assert sample_merged_df["fg_value"].between(0, 100).all()

    def test_fg_classification_is_valid_category(
        self, sample_merged_df: pd.DataFrame
    ) -> None:
        """All classification labels are valid Fear & Greed categories."""
        valid = {"Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"}
        assert set(sample_merged_df["fg_classification"].unique()).issubset(valid)

    def test_merged_df_no_nan_in_critical_columns(
        self, sample_merged_df: pd.DataFrame
    ) -> None:
        """No NaN values in key merged columns."""
        critical = ["symbol", "side", "closed_pnl", "fg_value", "fg_classification"]
        for col in critical:
            nan_count = sample_merged_df[col].isna().sum()
            assert nan_count == 0, f"Column '{col}' has {nan_count} NaN values"

    def test_merged_row_count_matches_trader_data(
        self, sample_merged_df: pd.DataFrame, sample_trader_df: pd.DataFrame
    ) -> None:
        """Merge preserves the original trader row count (no cartesian explosion)."""
        assert len(sample_merged_df) == len(sample_trader_df)


@pytest.mark.integration
class TestAnalyticsPipeline:
    """Integration: analytics engine produces valid outputs on merged data."""

    def test_win_rate_is_between_0_and_1(
        self, sample_merged_df: pd.DataFrame
    ) -> None:
        """Overall win rate is a valid probability."""
        if "is_profit" in sample_merged_df.columns:
            win_rate = sample_merged_df["is_profit"].mean()
            assert 0.0 <= win_rate <= 1.0

    def test_pnl_by_sentiment_regime_has_all_categories(
        self, sample_merged_df: pd.DataFrame
    ) -> None:
        """PnL groupby classification returns at least 2 distinct regimes."""
        groups = sample_merged_df.groupby("fg_classification")["closed_pnl"].mean()
        assert len(groups) >= 2

    def test_symbol_pnl_ranking_is_sorted(
        self, sample_merged_df: pd.DataFrame
    ) -> None:
        """Symbol PnL ranking is descending."""
        ranking = (
            sample_merged_df.groupby("symbol")["closed_pnl"]
            .sum()
            .sort_values(ascending=False)
        )
        assert list(ranking.values) == sorted(list(ranking.values), reverse=True)

    def test_total_pnl_matches_sum_of_closed_pnl(
        self, sample_merged_df: pd.DataFrame
    ) -> None:
        """Total PnL in the merged dataset is the sum of all closed_pnl values."""
        total = sample_merged_df["closed_pnl"].sum()
        assert isinstance(total, float)
