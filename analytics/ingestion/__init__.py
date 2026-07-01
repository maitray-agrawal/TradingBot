"""Dataset Ingestion Package for PrimeTrade AI.

Provides the complete suite of ingestion services: automatic schema classification,
header normalization, date standardizer, data quality validation, file scanning,
dashboard upload handling, and metadata profiling.
"""

from analytics.ingestion.dataset_detector import DatasetDetector
from analytics.ingestion.dataset_registry import DatasetRegistry
from analytics.ingestion.file_scanner import FileScanner
from analytics.ingestion.loader import IngestionEngine
from analytics.ingestion.metadata import (Dataset, DatasetMetadata,
                                          QualityReport, ValidationResult)
from analytics.ingestion.schema_mapper import DEFAULT_COLUMN_MAP, SchemaMapper
from analytics.ingestion.upload_handler import UploadHandler
from analytics.ingestion.validator import DatasetValidator

__all__ = [
    "DatasetDetector",
    "DatasetRegistry",
    "FileScanner",
    "IngestionEngine",
    "Dataset",
    "DatasetMetadata",
    "QualityReport",
    "ValidationResult",
    "SchemaMapper",
    "DEFAULT_COLUMN_MAP",
    "UploadHandler",
    "DatasetValidator",
]
