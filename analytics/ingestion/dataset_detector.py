"""Automatic dataset classification and type detection."""

import logging
from typing import List, Set, Tuple

import pandas as pd

from config.enums import DatasetType
from utils.logger import get_logger

logger = get_logger("analytics")


class DatasetDetector:
    """Detects and classifies datasets based on their column schemas."""

    # Target sets for overlap calculation (using normalized alphanumeric lowercase strings)
    TRADER_HISTORY_TARGETS: Set[str] = {
        "account",
        "coin",
        "symbol",
        "price",
        "executionprice",
        "closedpnl",
        "side",
        "size",
        "timestamp",
    }

    FEAR_GREED_TARGETS: Set[str] = {
        "classification",
        "value",
        "date",
        "timestamp",
    }

    def __init__(self, overlap_threshold: float = 0.25) -> None:
        """Initializes the detector.

        Args:
            overlap_threshold: Minimum overlap percentage (0.0 to 1.0) required for classification.
        """
        self.overlap_threshold = overlap_threshold

    def _normalize_header(self, header: str) -> str:
        """Normalizes a raw column header to lowercase alphanumeric for lookup.

        Args:
            header: Raw column string.

        Returns:
            Normalized lowercase header.
        """
        return "".join(c for c in header.lower() if c.isalnum())

    def detect_schema_type(self, columns: List[str]) -> Tuple[DatasetType, float]:
        """Classifies a schema list into a DatasetType and returns the confidence score.

        Args:
            columns: Raw column headers from a dataset.

        Returns:
            Tuple of (DatasetType, overlap_score).
        """
        if not columns:
            return DatasetType.UNKNOWN, 0.0

        normalized_cols = {self._normalize_header(col) for col in columns}

        # Calculate intersections
        trader_intersection = normalized_cols.intersection(self.TRADER_HISTORY_TARGETS)
        fg_intersection = normalized_cols.intersection(self.FEAR_GREED_TARGETS)

        trader_score = len(trader_intersection) / len(self.TRADER_HISTORY_TARGETS)
        fg_score = len(fg_intersection) / len(self.FEAR_GREED_TARGETS)

        logger.debug(
            f"Schema detection overlap scores -> Trader History: {trader_score:.2%}, "
            f"Fear & Greed: {fg_score:.2%}"
        )

        # Classify based on highest score exceeding threshold
        if trader_score >= fg_score and trader_score >= self.overlap_threshold:
            return DatasetType.TRADER_HISTORY, trader_score
        elif fg_score > trader_score and fg_score >= self.overlap_threshold:
            return DatasetType.FEAR_GREED, fg_score

        return DatasetType.UNKNOWN, 0.0

    def detect_dataframe_type(self, df: pd.DataFrame) -> DatasetType:
        """Detects the DatasetType of a pandas DataFrame.

        Args:
            df: The loaded pandas DataFrame.

        Returns:
            Classified DatasetType.
        """
        dtype, score = self.detect_schema_type(list(df.columns))
        logger.info(f"DataFrame classified as {dtype} with score {score:.2%}")
        return dtype
