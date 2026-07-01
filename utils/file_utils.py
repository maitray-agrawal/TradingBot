"""Generic file utility helpers for PrimeTrade AI.

Contains re-usable operations for scanning directories, verifying extensions,
calculating checksums, and checking sizes.
"""

import hashlib
import logging
from pathlib import Path
from typing import List, Union

logger = logging.getLogger("system")


def list_files_by_pattern(directory: Union[str, Path], pattern: str) -> List[Path]:
    """Lists files matching a glob pattern in a target directory.

    Args:
        directory: Path to the target directory.
        pattern: Glob pattern string (e.g. '*.csv').

    Returns:
        List of matching Path objects.
    """
    path = Path(directory)
    if not path.is_dir():
        logger.warning(
            f"Target directory {directory} does not exist or is not a folder."
        )
        return []
    return list(path.glob(pattern))


def verify_file_exists(file_path: Union[str, Path]) -> bool:
    """Verifies if a target path is an existing file.

    Args:
        file_path: Path to check.

    Returns:
        True if path exists and is a file, False otherwise.
    """
    return Path(file_path).is_file()


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Calculates the size of a file in Megabytes.

    Args:
        file_path: Path to the target file.

    Returns:
        File size in MB (float).
    """
    path = Path(file_path)
    if not path.is_file():
        return 0.0
    return path.stat().st_size / (1024 * 1024)


def get_file_sha256(file_path: Union[str, Path]) -> str:
    """Computes the SHA256 checksum of a file.

    Args:
        file_path: Path to the target file.

    Returns:
        Hexadecimal SHA256 checksum string.
    """
    sha256 = hashlib.sha256()
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read in chunks of 64KB
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
