import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from config.settings import settings
from utils.logger import analytics_logger, system_logger


class DatasetType(str, Enum):
    FEAR_GREED = "fear_greed"
    TRADER_DATA = "trader_data"
    UNKNOWN = "unknown"


class DatasetDetector:
    """
    Scans the data directory and detects CSV, XLSX, JSON, and Parquet datasets.
    Automatically classifies datasets as either Fear & Greed Index or Historical Trader Data.
    """

    # Target columns normalized (lowercased, spaces/underscores removed)
    FEAR_GREED_TARGETS = {"classification", "value", "date", "timestamp"}
    TRADER_DATA_TARGETS = {
        "account",
        "coin",
        "symbol",
        "price",
        "executionprice",
        "closedpnl",
        "profit",
        "pnl",
        "side",
        "size",
        "timestamp",
    }

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        analytics_logger.info(
            f"DatasetDetector initialized targeting directory: {self.data_dir}"
        )

    @staticmethod
    def normalize_header(header: str) -> str:
        """Normalize header names to lowercase with no spaces or underscores."""
        return str(header).strip().lower().replace("_", "").replace(" ", "")

    def scan_files(self) -> List[Path]:
        """Scan the data directory for CSV, XLSX, JSON, and Parquet files."""
        if not self.data_dir.exists():
            analytics_logger.warning(f"Data directory {self.data_dir} does not exist.")
            return []

        extensions = {".csv", ".xlsx", ".json", ".parquet"}
        files = []
        for file in self.data_dir.iterdir():
            if file.is_file() and file.suffix.lower() in extensions:
                files.append(file)
        analytics_logger.info(f"Found {len(files)} candidate files in data directory.")
        return files

    def get_headers(self, file_path: Path) -> List[str]:
        """Read the headers/columns of a dataset file without loading the full file."""
        suffix = file_path.suffix.lower()
        try:
            if suffix == ".csv":
                df = pd.read_csv(file_path, nrows=1)
                return list(df.columns)
            elif suffix == ".xlsx":
                df = pd.read_excel(file_path, nrows=1)
                return list(df.columns)
            elif suffix == ".json":
                df = pd.read_json(file_path, nrows=1)
                return list(df.columns)
            elif suffix == ".parquet":
                df = pd.read_parquet(file_path, nrows=1)
                return list(df.columns)
        except Exception as e:
            analytics_logger.error(f"Failed to read headers from {file_path}: {e}")
            return []
        return []

    def classify_dataset(self, file_path: Path) -> Tuple[DatasetType, float]:
        """
        Classifies a file based on column matching score.
        Returns (DatasetType, score).
        """
        headers = self.get_headers(file_path)
        if not headers:
            return DatasetType.UNKNOWN, 0.0

        normalized_headers = {self.normalize_header(h) for h in headers}

        # Calculate overlap scores
        fg_matches = normalized_headers.intersection(self.FEAR_GREED_TARGETS)
        trader_matches = normalized_headers.intersection(self.TRADER_DATA_TARGETS)

        fg_score = (
            len(fg_matches) / len(self.FEAR_GREED_TARGETS)
            if self.FEAR_GREED_TARGETS
            else 0.0
        )
        trader_score = (
            len(trader_matches) / len(self.TRADER_DATA_TARGETS)
            if self.TRADER_DATA_TARGETS
            else 0.0
        )

        analytics_logger.debug(
            f"File: {file_path.name} | FG overlap: {len(fg_matches)} (Score: {fg_score:.2f}) | "
            f"Trader overlap: {len(trader_matches)} (Score: {trader_score:.2f})"
        )

        threshold = 0.25  # Require at least 25% overlap
        if fg_score > trader_score and fg_score >= threshold:
            return DatasetType.FEAR_GREED, fg_score
        elif trader_score > fg_score and trader_score >= threshold:
            return DatasetType.TRADER_DATA, trader_score

        return DatasetType.UNKNOWN, 0.0

    def detect_all_datasets(self) -> Dict[DatasetType, List[Dict[str, Any]]]:
        """
        Scans, classifies, and returns detected datasets.
        """
        files = self.scan_files()
        results = {
            DatasetType.FEAR_GREED: [],
            DatasetType.TRADER_DATA: [],
            DatasetType.UNKNOWN: [],
        }

        for file_path in files:
            dtype, score = self.classify_dataset(file_path)
            file_info = {
                "path": file_path,
                "name": file_path.name,
                "format": file_path.suffix[1:].upper(),
                "score": score,
            }
            results[dtype].append(file_info)

        analytics_logger.info(
            f"Classification Results - Fear&Greed: {len(results[DatasetType.FEAR_GREED])}, "
            f"TraderData: {len(results[DatasetType.TRADER_DATA])}, Unknown: {len(results[DatasetType.UNKNOWN])}"
        )
        return results

    def select_dataset_cli(
        self, dataset_type: DatasetType, candidates: List[Dict[str, Any]]
    ) -> Optional[Path]:
        """
        Prompts user via CLI menu to select from multiple candidates for a dataset type.
        """
        if not candidates:
            return None
        if len(candidates) == 1:
            analytics_logger.info(
                f"Auto-selected single candidate for {dataset_type.value}: {candidates[0]['name']}"
            )
            return candidates[0]["path"]

        print(f"\nMultiple candidates found for {dataset_type.value.upper()}:")
        for i, cand in enumerate(candidates):
            print(
                f"  [{i+1}] {cand['name']} (Format: {cand['format']}, Score: {cand['score']:.2f})"
            )

        while True:
            try:
                choice = input(f"Select dataset [1-{len(candidates)}]: ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(candidates):
                    selected = candidates[idx]["path"]
                    analytics_logger.info(
                        f"User selected {dataset_type.value}: {selected.name}"
                    )
                    return selected
                else:
                    print("Invalid option. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
