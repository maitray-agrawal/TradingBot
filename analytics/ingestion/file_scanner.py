"""Scanner utility to identify and classify files in target data folders."""

import os
from pathlib import Path
from typing import Dict, List
from typing import Optional, List

import pandas as pd

try:
    import pyarrow.parquet as pq
except ImportError:
    pq = None

from analytics.ingestion.dataset_detector import DatasetDetector
from config.enums import DatasetType
from config.paths import RAW_DATA_DIR, UPLOADS_DATA_DIR
from utils.logger import get_logger

logger = get_logger("analytics")


class FileScanner:
    """Scans and inventory data folders for files and detects their types."""

    SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".json", ".parquet"}

    def __init__(
        self,
        detector: Optional[DatasetDetector] = None,
        search_dirs: Optional[List[Path]] = None,
    ) -> None:
        """Initializes the scanner.

        Args:
            detector: Optional DatasetDetector instance.
            search_dirs: Optional list of directory paths to scan.
        """
        self.detector = detector if detector is not None else DatasetDetector()
        self.search_dirs = search_dirs if search_dirs is not None else [RAW_DATA_DIR, UPLOADS_DATA_DIR]

    def scan_directories(self) -> Dict[str, DatasetType]:
        """Scans all configured search directories for supported files.

        Returns:
            Dictionary matching file absolute path to its detected DatasetType.
        """
        discovered: Dict[str, DatasetType] = {}

        for directory in self.search_dirs:
            if not directory.exists():
                logger.warning(f"Scan directory does not exist: {directory}")
                continue

            logger.info(f"Scanning directory: {directory}")
            for entry in os.scandir(directory):
                if entry.is_file():
                    file_path = Path(entry.path)
                    ext = file_path.suffix.lower()

                    if ext in self.SUPPORTED_EXTENSIONS:
                        try:
                            cols = self.peek_columns(file_path)
                            dtype, score = self.detector.detect_schema_type(cols)
                            discovered[str(file_path.resolve())] = dtype
                            logger.info(
                                f"Discovered file: {file_path.name} -> Classified as {dtype.name} (score: {score:.2%})"
                            )
                        except Exception as e:
                            logger.error(f"Failed to peek columns of file {file_path.name}: {e}")
                            discovered[str(file_path.resolve())] = DatasetType.UNKNOWN

        return discovered

    def peek_columns(self, file_path: Path) -> List[str]:
        """Peeks at a file's headers without loading the full content.

        Args:
            file_path: Path to the target file.

        Returns:
            List of column name strings.
        """
        ext = file_path.suffix.lower()
        if not file_path.exists():
            return []

        if ext == ".csv":
            df = pd.read_csv(file_path, nrows=0)
            return list(df.columns)

        elif ext == ".xlsx":
            # For excel, read 0 rows
            df = pd.read_excel(file_path, nrows=0)
            return list(df.columns)

        elif ext == ".json":
            # Read first chunk or try to read 1 line or whole schema if small.
            # In pandas read_json doesn't support nrows, so read first row or load a tiny sample.
            # For JSON arrays:
            try:
                # Attempt to parse as standard array of records
                df = pd.read_json(file_path, nrows=1)
                return list(df.columns)
            except Exception:
                # fallback: load entire file if it's small, or read the columns of a standard load
                df = pd.read_json(file_path)
                return list(df.columns)

        elif ext == ".parquet":
            if pq is not None:
                schema = pq.read_schema(file_path)
                return schema.names
            else:
                df = pd.read_parquet(file_path, columns=[])
                return list(df.columns)

        return []
