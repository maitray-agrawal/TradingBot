"""Data validation utilities for loaded datasets."""

import os
from typing import List, Optional

import pandas as pd

from analytics.ingestion.metadata import ValidationResult
from config.enums import DatasetType
from utils.exceptions import DatasetError, ValidationError
from utils.logger import get_logger

logger = get_logger("analytics")


class DatasetValidator:
    """Validates structural integrity, formats, and schemas of datasets."""

    def __init__(self, max_file_size_mb: float = 50.0) -> None:
        """Initializes the validator.

        Args:
            max_file_size_mb: Maximum allowed file size in Megabytes.
        """
        self.max_file_size_mb = max_file_size_mb

    def validate_file_size(self, file_path: str) -> None:
        """Checks if a file exceeds the size threshold.

        Args:
            file_path: Absolute path to the file.

        Raises:
            ValidationError: If the file exceeds the size limit.
        """
        if not os.path.exists(file_path):
            raise ValidationError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValidationError("File is empty (contains 0 bytes).")

        file_size_mb = file_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValidationError(
                f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed limit ({self.max_file_size_mb} MB)"
            )

    def run_checks(
        self,
        df: pd.DataFrame,
        dataset_type: DatasetType,
        raw_columns: List[str],
    ) -> ValidationResult:
        """Performs a comprehensive set of validations on the DataFrame.

        Args:
            df: Standardized DataFrame to validate.
            dataset_type: Detected type of the dataset.
            raw_columns: List of columns before standardization.

        Returns:
            ValidationResult summarizing found errors, warnings, and executed steps.
        """
        errors: List[str] = []
        warnings: List[str] = []
        logs: List[str] = []

        # 1. Empty Check
        logs.append("Executing empty structure check.")
        if df.empty or len(df.columns) == 0:
            errors.append("Dataset is empty; contains zero rows or zero columns.")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings, check_logs=logs)

        # 2. Duplicate Columns Check
        logs.append("Executing duplicate headers check.")
        import re

        lower_cols = [re.sub(r"\.\d+$", "", str(c).lower().strip()) for c in raw_columns]
        if len(lower_cols) != len(set(lower_cols)):
            dups = set([c for c in lower_cols if lower_cols.count(c) > 1])
            errors.append(f"Duplicate column headers detected: {dups}")

        # 3. Duplicate Rows Check
        logs.append("Executing duplicate rows check.")
        dup_rows = df.duplicated().sum()
        if dup_rows > 0:
            warnings.append(f"Dataset contains {dup_rows} identical duplicate rows.")

        # 4. Missing Required Columns Check
        logs.append(f"Executing required columns check for dataset type {dataset_type.name}.")
        if dataset_type == DatasetType.TRADER_HISTORY:
            # Critical columns needed for downstream logic
            required = ["symbol", "side", "size", "execution_price", "timestamp"]
            missing = [r for r in required if r not in df.columns]
            if missing:
                errors.append(f"Trader History dataset is missing required columns: {missing}")

        elif dataset_type == DatasetType.FEAR_GREED:
            # Critical columns for daily index
            required = ["classification", "value", "timestamp"]
            missing = [r for r in required if r not in df.columns]
            if missing:
                errors.append(f"Fear & Greed dataset is missing required columns: {missing}")

        # 5. Invalid Timestamps Check
        logs.append("Executing timestamp column check.")
        if "timestamp" in df.columns:
            null_timestamps = df["timestamp"].isna().sum()
            if null_timestamps == len(df):
                errors.append("Timestamp column is entirely null or contains unparseable dates.")
            elif null_timestamps > 0:
                warnings.append(f"Timestamp column has {null_timestamps} missing/unparseable values.")

        # 6. Unsupported Datatypes Check
        logs.append("Executing column datatypes safety check.")
        for col in df.columns:
            col_type = df[col].dtype
            if str(col_type) in ("object", "string"):
                # Non-text object types (like lists, dicts, tuples) are unsupported
                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if sample is not None and isinstance(sample, (list, dict, tuple, set)):
                    errors.append(f"Column '{col}' contains unsupported complex nested datatype: {type(sample)}")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings, check_logs=logs)
