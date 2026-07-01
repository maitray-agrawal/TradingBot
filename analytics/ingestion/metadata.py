"""Data models and structures for dataset ingestion."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

import pandas as pd

from config.enums import DatasetType


@dataclass(frozen=True)
class DatasetMetadata:
    """Detailed structural statistics and metadata of a loaded dataset."""

    rows: int
    columns: int
    column_types: Dict[str, str]
    null_counts: Dict[str, int]
    duplicate_count: int
    memory_usage_bytes: int
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    file_size_bytes: int
    file_checksum: str
    last_modified: str
    load_time_seconds: float
    target_columns_found: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of dataset structure and semantic validations."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    check_logs: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class QualityReport:
    """Quality analysis report identifying potential anomalies and recommendations."""

    quality_score: float  # Scale from 0.0 to 100.0
    potential_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class Dataset:
    """Complete domain object encapsulating a loaded dataset and its profile.

    Attributes:
        dataframe: The loaded and cleaned pandas DataFrame.
        metadata: Detailed structural and type statistics.
        dataset_type: Classification label (TRADER_HISTORY, FEAR_GREED, UNKNOWN).
        quality_report: Quality score, warnings, and suggestions.
        column_mapping: Mapping of original to standardized headers.
        validation_result: Complete checklist of integrity rules executed.
    """

    dataframe: pd.DataFrame
    metadata: DatasetMetadata
    dataset_type: DatasetType
    quality_report: QualityReport
    column_mapping: Dict[str, str]
    validation_result: ValidationResult
