"""Unified utility package for PrimeTrade AI."""

from utils.config_utils import load_json_config, save_json_config
from utils.dataframe_utils import (
    clean_column_names,
    detect_outliers_iqr,
    get_missing_value_report,
)
from utils.exceptions import (
    APIError,
    AnalyticsError,
    ConfigurationError,
    DatasetError,
    NetworkError,
    ProjectError,
    TradingBotError,
    ValidationError,
)
from utils.file_utils import (
    get_file_sha256,
    get_file_size_mb,
    list_files_by_pattern,
    verify_file_exists,
)
from utils.logger import setup_logging
from utils.time_utils import (
    format_datetime_to_string,
    get_current_utc_datetime,
    get_current_utc_timestamp,
    parse_timestamp_to_datetime,
)
from utils.validation_utils import (
    validate_decimal_precision,
    validate_in_range,
    validate_is_positive,
)

__all__ = [
    # Logger
    "setup_logging",
    # Exceptions
    "ProjectError",
    "DatasetError",
    "ValidationError",
    "ConfigurationError",
    "TradingBotError",
    "AnalyticsError",
    "NetworkError",
    "APIError",
    # File Utils
    "list_files_by_pattern",
    "verify_file_exists",
    "get_file_size_mb",
    "get_file_sha256",
    # Time Utils
    "parse_timestamp_to_datetime",
    "format_datetime_to_string",
    "get_current_utc_timestamp",
    "get_current_utc_datetime",
    # DataFrame Utils
    "clean_column_names",
    "get_missing_value_report",
    "detect_outliers_iqr",
    # Validation Utils
    "validate_in_range",
    "validate_is_positive",
    "validate_decimal_precision",
    # Config Utils
    "load_json_config",
    "save_json_config",
]
