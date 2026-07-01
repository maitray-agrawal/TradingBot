"""Core dataset loader and orchestration engine for ingestion."""

import hashlib
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from analytics.ingestion.dataset_detector import DatasetDetector
from analytics.ingestion.dataset_registry import DatasetRegistry
from analytics.ingestion.metadata import Dataset, DatasetMetadata, QualityReport, ValidationResult
from analytics.ingestion.schema_mapper import SchemaMapper
from analytics.ingestion.validator import DatasetValidator
from config.enums import DatasetType
from utils.exceptions import DatasetError, ValidationError
from utils.file_utils import get_file_sha256
from utils.logger import get_logger

logger = get_logger("analytics")


class IngestionEngine:
    """The master entry point for loading, standardizing, validating, and profiling datasets."""

    def __init__(
        self,
        detector: Optional[DatasetDetector] = None,
        mapper: Optional[SchemaMapper] = None,
        validator: Optional[DatasetValidator] = None,
        registry: Optional[DatasetRegistry] = None,
    ) -> None:
        """Initializes the ingestion engine with required components."""
        self.detector = detector if detector is not None else DatasetDetector()
        self.mapper = mapper if mapper is not None else SchemaMapper()
        self.validator = validator if validator is not None else DatasetValidator()
        self.registry = registry if registry is not None else DatasetRegistry()

    def _infer_file_type(self, file_path: Path) -> str:
        """Infers the extension and format of the target file.

        Args:
            file_path: Path object of the file.

        Returns:
            Lowercase extension representation.
        """
        suffix = file_path.suffix.lower()
        if suffix in (".csv", ".xlsx", ".json", ".parquet"):
            return suffix
        raise ValidationError(f"Unsupported file format extension: {suffix}")

    def _read_file(self, file_path: Path, file_type: str) -> pd.DataFrame:
        """Reads a file into a pandas DataFrame based on inferred file type.

        Args:
            file_path: File Path.
            file_type: Inferred file type extension (e.g. '.csv').

        Returns:
            Parsed pandas DataFrame.

        Raises:
            DatasetError: If reading or parsing the file content fails.
        """
        try:
            if file_type == ".csv":
                return pd.read_csv(file_path)
            elif file_type == ".xlsx":
                return pd.read_excel(file_path)
            elif file_type == ".json":
                # Accept both record-based and standard nested JSON structures
                try:
                    return pd.read_json(file_path, orient="records")
                except Exception:
                    return pd.read_json(file_path)
            elif file_type == ".parquet":
                return pd.read_parquet(file_path)
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise DatasetError(f"Corrupted or unreadable file: {e}")

        raise ValidationError(f"File type {file_type} is not supported by read routine.")

    def _auto_detect_and_convert_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Finds date/timestamp columns and standardizes them to timezone-naive datetime.

        Args:
            df: Standardized DataFrame.

        Returns:
            DataFrame with converted datetime columns.
        """
        for col in df.columns:
            col_str = str(col).lower()
            col_type = df[col].dtype

            # Identify if column name indicates date/time, or is already datetime, or contains UNIX values
            is_date_col = "date" in col_str or "time" in col_str or "timestamp" in col_str or "epoch" in col_str

            if is_date_col or str(col_type).startswith("datetime"):
                logger.debug(f"Auto-detecting datetime format for column: {col}")
                try:
                    sample = df[col].dropna()
                    if sample.empty:
                        # Empty date column, just cast to datetime format
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                        continue

                    first_val = sample.iloc[0]

                    # Numeric UNIX timestamp detection
                    if isinstance(first_val, (int, float)) or str(col_type).startswith(("int", "float")):
                        # Verify if UNIX milliseconds or UNIX seconds
                        # Mean values > 1e11 indicate millisecond timestamps (Binance format)
                        mean_val = sample.mean()
                        if mean_val > 1e11:
                            df[col] = pd.to_datetime(df[col], unit="ms", errors="coerce")
                        else:
                            df[col] = pd.to_datetime(df[col], unit="s", errors="coerce")
                    else:
                        # String parser
                        df[col] = pd.to_datetime(df[col], errors="coerce")

                    # Strip timezones to make timezone-naive (prevent timezone merge conflict errors)
                    if hasattr(df[col], "dt"):
                        if df[col].dt.tz is not None:
                            df[col] = df[col].dt.tz_localize(None)

                except Exception as e:
                    logger.warning(f"Could not convert column '{col}' to datetime: {e}")

        return df

    def _build_metadata(
        self,
        df: pd.DataFrame,
        file_path: Path,
        checksum: str,
        load_time: float,
        target_columns: List[str],
    ) -> DatasetMetadata:
        """Compiles structure, sizing, and schema statistics from the loaded DataFrame."""
        rows, columns = df.shape
        col_types = {col: str(df[col].dtype) for col in df.columns}
        null_counts = {col: int(df[col].isna().sum()) for col in df.columns}
        duplicate_count = int(df.duplicated().sum())
        memory_usage_bytes = int(df.memory_usage(deep=True).sum())
        file_size_bytes = os.path.getsize(file_path)
        last_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

        numeric_cols = []
        categorical_cols = []
        datetime_cols = []

        for col in df.columns:
            dtype_str = str(df[col].dtype)
            if dtype_str.startswith(("int", "float")):
                numeric_cols.append(col)
            elif dtype_str.startswith("datetime"):
                datetime_cols.append(col)
            else:
                categorical_cols.append(col)

        return DatasetMetadata(
            rows=rows,
            columns=columns,
            column_types=col_types,
            null_counts=null_counts,
            duplicate_count=duplicate_count,
            memory_usage_bytes=memory_usage_bytes,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            datetime_columns=datetime_cols,
            file_size_bytes=file_size_bytes,
            file_checksum=checksum,
            last_modified=last_modified,
            load_time_seconds=load_time,
            target_columns_found=target_columns,
        )

    def _generate_quality_report(
        self, df: pd.DataFrame, dataset_type: DatasetType, validation: ValidationResult
    ) -> QualityReport:
        """Profiles the dataset to calculate a quality score and recommendations."""
        score = 100.0
        issues: List[str] = []
        recommendations: List[str] = []

        # Empty Check
        if df.empty:
            return QualityReport(
                quality_score=0.0,
                potential_issues=["Empty dataset"],
                recommendations=["Upload a valid non-empty file."],
            )

        # Deduct for duplicate rows
        dup_rows = int(df.duplicated().sum())
        if dup_rows > 0:
            dup_pct = (dup_rows / len(df)) * 100
            deduction = min(20.0, dup_pct * 0.5 + 5.0)
            score -= deduction
            issues.append(f"Contains duplicate rows: {dup_rows} ({dup_pct:.2f}%)")
            recommendations.append("Apply row deduplication preprocessing.")

        # Deduct for missing values
        total_cells = df.size
        total_nulls = df.isna().sum().sum()
        if total_nulls > 0:
            null_pct = (total_nulls / total_cells) * 100
            deduction = min(30.0, null_pct * 0.8)
            score -= deduction
            issues.append(f"Contains missing/null cell values: {total_nulls} ({null_pct:.2f}%)")
            recommendations.append("Impute or filter out null observations.")

        # Check critical fields depending on dataset type
        if dataset_type == DatasetType.TRADER_HISTORY:
            for col in ["execution_price", "size", "side", "timestamp"]:
                if col in df.columns:
                    col_nulls = df[col].isna().sum()
                    if col_nulls > 0:
                        score -= 15.0
                        issues.append(f"Critical trade column '{col}' has {col_nulls} null entries.")
                        recommendations.append(f"Clean or filter incomplete values in '{col}'.")

                    # Check for anomalous negative prices or sizes
                    if col in ("execution_price", "size") and df[col].dtype.kind in "ijf":
                        negatives = (df[col] <= 0).sum()
                        if negatives > 0:
                            score -= 10.0
                            issues.append(f"Column '{col}' contains negative or zero values: {negatives} records.")
                            recommendations.append(f"Filter out zero or negative observations in '{col}'.")

        elif dataset_type == DatasetType.FEAR_GREED:
            for col in ["value", "classification", "timestamp"]:
                if col in df.columns:
                    col_nulls = df[col].isna().sum()
                    if col_nulls > 0:
                        score -= 15.0
                        issues.append(f"Critical sentiment column '{col}' has {col_nulls} null entries.")
                        recommendations.append(f"Clean or filter incomplete values in '{col}'.")

                    # Check value bounds (0-100)
                    if col == "value" and df[col].dtype.kind in "ijf":
                        out_of_bounds = ((df[col] < 0) | (df[col] > 100)).sum()
                        if out_of_bounds > 0:
                            score -= 10.0
                            issues.append(f"Sentiment 'value' out of standard 0-100 bounds: {out_of_bounds} records.")
                            recommendations.append("Clamp sentiment index values between 0 and 100.")

        # Cap score between 0 and 100
        final_score = max(0.0, min(100.0, score))

        if final_score > 90.0:
            recommendations.append("Dataset structure looks excellent. Ready for analytical pipeline.")

        return QualityReport(
            quality_score=final_score,
            potential_issues=issues,
            recommendations=recommendations,
        )

    def load_dataset(self, file_path: str, dataset_name: Optional[str] = None) -> Dataset:
        """Loads, standardizes, validates, and registers a dataset from a file path.

        Args:
            file_path: Absolute path to target CSV, Excel, JSON, or Parquet file.
            dataset_name: Optional name for registration (defaults to file basename).

        Returns:
            The loaded Dataset domain object.

        Raises:
            ValidationError: If size checks, duplicate column validations, or schema checks fail.
            DatasetError: If file is corrupted or unreadable.
        """
        start_time = time.perf_counter()
        path = Path(file_path).resolve()
        name = dataset_name if dataset_name is not None else path.name

        logger.info(f"Initiating dataset ingestion for: {name} ({path})")

        # 1. File Sizing Validation
        self.validator.validate_file_size(str(path))

        # 2. Checksum and Info
        checksum = get_file_sha256(path)
        file_type = self._infer_file_type(path)

        # 3. Read raw data
        raw_df = self._read_file(path, file_type)
        raw_columns = list(raw_df.columns)
        logger.info(f"Loaded raw file. Shape: {raw_df.shape}")

        # 4. Standardize Columns
        standardized_df, mapping = self.mapper.standardize_dataframe(raw_df)

        # 5. Detect Dataset Type
        detected_type = self.detector.detect_dataframe_type(standardized_df)
        logger.info(f"Classified dataset '{name}' as type: {detected_type.name}")

        # 6. Auto DateTime Standardizations
        standardized_df = self._auto_detect_and_convert_dates(standardized_df)

        # 7. Run validations
        validation = self.validator.run_checks(standardized_df, detected_type, raw_columns)

        if not validation.is_valid:
            logger.error(f"Validation failed for dataset {name}: {validation.errors}")
            raise ValidationError(
                f"Validation failed for dataset '{name}': {validation.errors}",
                details={"errors": validation.errors, "warnings": validation.warnings},
            )

        # 8. Build stats & metadata
        load_time = time.perf_counter() - start_time
        target_cols = [col for col in standardized_df.columns if col in mapping.values()]
        metadata = self._build_metadata(standardized_df, path, checksum, load_time, target_cols)

        # 9. Profile Quality
        quality = self._generate_quality_report(standardized_df, detected_type, validation)

        # 10. Register Dataset
        self.registry.register(name, str(path), detected_type.value, metadata)

        logger.info(
            f"Ingestion finalized for '{name}' in {load_time:.4f}s. " f"Quality Score: {quality.quality_score:.1f}/100"
        )

        return Dataset(
            dataframe=standardized_df,
            metadata=metadata,
            dataset_type=detected_type,
            quality_report=quality,
            column_mapping=mapping,
            validation_result=validation,
        )
