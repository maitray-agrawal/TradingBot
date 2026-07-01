"""Unit tests for the Dataset Ingestion Engine (Phase 2)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from analytics.ingestion import (DatasetRegistry, DatasetValidator,
                                 FileScanner, IngestionEngine, SchemaMapper,
                                 UploadHandler)
from config.enums import DatasetType
from utils.exceptions import DatasetError, ValidationError


@pytest.fixture
def temp_registry(tmp_path: Path) -> DatasetRegistry:
    """Fixture providing a temporary dataset registry file."""
    reg_file = tmp_path / "registry.json"
    return DatasetRegistry(registry_file=str(reg_file))


@pytest.fixture
def ingestion_engine(temp_registry: DatasetRegistry) -> IngestionEngine:
    """Fixture providing a configured IngestionEngine."""
    return IngestionEngine(registry=temp_registry)


@pytest.fixture
def mock_trader_df() -> pd.DataFrame:
    """Fixture providing mock Trader History data."""
    return pd.DataFrame(
        {
            "Account": ["ACC-1", "ACC-1"],
            "Coin": ["BTC", "ETH"],
            "Execution Price": [30000.5, 1850.0],
            "Side": ["BUY", "SELL"],
            "Size": [0.1, 2.0],
            "Closed PnL": [0.0, 150.0],
            "Timestamp": [1688212800000, 1688299200000],  # millisecond unix
        }
    )


@pytest.fixture
def mock_fear_greed_df() -> pd.DataFrame:
    """Fixture providing mock Fear & Greed Index data."""
    return pd.DataFrame(
        {
            "date": ["2023-07-01", "2023-07-02"],
            "value": [30.0, 65.0],
            "classification": ["Fear", "Greed"],
            "timestamp": [1688212800, 1688299200],  # seconds unix
        }
    )


def test_csv_ingestion(
    tmp_path: Path, ingestion_engine: IngestionEngine, mock_trader_df: pd.DataFrame
) -> None:
    """Tests loading a valid CSV trader history dataset."""
    file_path = tmp_path / "trader_history.csv"
    mock_trader_df.to_csv(file_path, index=False)

    dataset = ingestion_engine.load_dataset(str(file_path))

    assert dataset.dataset_type == DatasetType.TRADER_HISTORY
    assert dataset.metadata.rows == 2
    assert "execution_price" in dataset.dataframe.columns
    assert "closed_pnl" in dataset.dataframe.columns
    # Check timezone-naive conversion
    assert pd.api.types.is_datetime64_any_dtype(dataset.dataframe["timestamp"])
    assert dataset.validation_result.is_valid is True
    assert dataset.quality_report.quality_score > 80.0


def test_excel_ingestion(
    tmp_path: Path, ingestion_engine: IngestionEngine, mock_fear_greed_df: pd.DataFrame
) -> None:
    """Tests loading a valid Excel sentiment dataset."""
    file_path = tmp_path / "fear_greed.xlsx"
    mock_fear_greed_df.to_excel(file_path, index=False)

    dataset = ingestion_engine.load_dataset(str(file_path))

    assert dataset.dataset_type == DatasetType.FEAR_GREED
    assert "value" in dataset.dataframe.columns
    assert "classification" in dataset.dataframe.columns
    assert pd.api.types.is_datetime64_any_dtype(dataset.dataframe["timestamp"])
    assert dataset.validation_result.is_valid is True


def test_json_ingestion(
    tmp_path: Path, ingestion_engine: IngestionEngine, mock_trader_df: pd.DataFrame
) -> None:
    """Tests loading a valid JSON dataset."""
    file_path = tmp_path / "trader.json"
    mock_trader_df.to_json(file_path, orient="records")

    dataset = ingestion_engine.load_dataset(str(file_path))
    assert dataset.dataset_type == DatasetType.TRADER_HISTORY
    assert dataset.metadata.rows == 2


def test_parquet_ingestion(
    tmp_path: Path, ingestion_engine: IngestionEngine, mock_trader_df: pd.DataFrame
) -> None:
    """Tests loading a valid Parquet dataset."""
    file_path = tmp_path / "trader.parquet"
    mock_trader_df.to_parquet(file_path, index=False)

    dataset = ingestion_engine.load_dataset(str(file_path))
    assert dataset.dataset_type == DatasetType.TRADER_HISTORY
    assert dataset.metadata.rows == 2


def test_empty_file_validation(
    tmp_path: Path, ingestion_engine: IngestionEngine
) -> None:
    """Tests that empty file structures raise validation exceptions."""
    file_path = tmp_path / "empty.csv"
    # Create empty file
    file_path.touch()

    with pytest.raises(ValidationError, match="empty|Validation"):
        ingestion_engine.load_dataset(str(file_path))


def test_corrupted_file_validation(
    tmp_path: Path, ingestion_engine: IngestionEngine
) -> None:
    """Tests that corrupted content structures raise DatasetError exceptions."""
    file_path = tmp_path / "corrupted.json"
    with open(file_path, "w") as f:
        f.write("{invalid json content")

    with pytest.raises(DatasetError, match="Corrupted or unreadable file"):
        ingestion_engine.load_dataset(str(file_path))


def test_unknown_dataset_classification(
    tmp_path: Path, ingestion_engine: IngestionEngine
) -> None:
    """Tests that unknown schemas fall back to DatasetType.UNKNOWN."""
    df = pd.DataFrame({"random_col_1": [1, 2], "random_col_2": [3, 4]})
    file_path = tmp_path / "unknown.csv"
    df.to_csv(file_path, index=False)

    dataset = ingestion_engine.load_dataset(str(file_path))
    assert dataset.dataset_type == DatasetType.UNKNOWN
    # Validation will still be True because Unknown type doesn't have missing column requirements
    assert dataset.validation_result.is_valid is True


def test_duplicate_columns_validation(
    tmp_path: Path, ingestion_engine: IngestionEngine
) -> None:
    """Tests that duplicate column headers cause ingestion validation failures."""
    file_content = "Symbol,Symbol,Side,Size,Timestamp\nBTC,BTC,BUY,0.1,1688212800\n"
    file_path = tmp_path / "duplicate_cols.csv"
    with open(file_path, "w") as f:
        f.write(file_content)

    with pytest.raises(ValidationError, match="Duplicate column headers detected"):
        ingestion_engine.load_dataset(str(file_path))


def test_file_scanner(
    tmp_path: Path, mock_trader_df: pd.DataFrame, mock_fear_greed_df: pd.DataFrame
) -> None:
    """Tests directory scans and classification mappings."""
    # Setup test directories
    raw_dir = tmp_path / "raw"
    uploads_dir = tmp_path / "uploads"
    raw_dir.mkdir()
    uploads_dir.mkdir()

    # Write files
    mock_trader_df.to_csv(raw_dir / "trades.csv", index=False)
    mock_fear_greed_df.to_excel(uploads_dir / "sentiment.xlsx", index=False)
    # Unknown file
    pd.DataFrame({"a": [1]}).to_json(raw_dir / "unknown.json", orient="records")

    scanner = FileScanner(search_dirs=[raw_dir, uploads_dir])
    discovered = scanner.scan_directories()

    assert len(discovered) == 3
    # Check classifications
    trader_path = str((raw_dir / "trades.csv").resolve())
    fg_path = str((uploads_dir / "sentiment.xlsx").resolve())
    unknown_path = str((raw_dir / "unknown.json").resolve())

    assert discovered[trader_path] == DatasetType.TRADER_HISTORY
    assert discovered[fg_path] == DatasetType.FEAR_GREED
    assert discovered[unknown_path] == DatasetType.UNKNOWN


def test_upload_handler(
    tmp_path: Path, ingestion_engine: IngestionEngine, mock_trader_df: pd.DataFrame
) -> None:
    """Tests the dashboard upload processing pipeline."""
    # Override standard upload directory path to temp location
    import analytics.ingestion.upload_handler as uh

    old_dir = uh.UPLOADS_DATA_DIR
    uh.UPLOADS_DATA_DIR = tmp_path / "dashboard_uploads"

    try:
        handler = UploadHandler(ingestion_engine)
        # Prepare bytes
        csv_bytes = mock_trader_df.to_csv(index=False).encode("utf-8")

        dataset = handler.handle_upload("new_upload.csv", csv_bytes)

        assert dataset.dataset_type == DatasetType.TRADER_HISTORY
        assert (tmp_path / "dashboard_uploads" / "new_upload.csv").exists()
        assert ingestion_engine.registry.get("new_upload.csv") is not None
    finally:
        # Restore old upload directory path
        uh.UPLOADS_DATA_DIR = old_dir
