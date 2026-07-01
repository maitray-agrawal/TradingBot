"""Generic configuration persistence helpers for PrimeTrade AI.

Provides standard JSON file reading and writing routines with structured error
handlings and default fallback settings.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Union

logger = logging.getLogger("system")


def load_json_config(file_path: Union[str, Path], default: Dict[str, Any] = None) -> Dict[str, Any]:
    """Loads a JSON configuration file, falling back to a default dict if missing/invalid.

    Args:
        file_path: Target path to the JSON file.
        default: Default dictionary to return on failure.

    Returns:
        Dictionary configuration.
    """
    path = Path(file_path)
    fallback = default if default is not None else {}

    if not path.is_file():
        logger.warning(f"Config file not found: {file_path}. Using default configuration.")
        return fallback

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in {file_path}: {e}. Returning default settings.")
        return fallback
    except Exception as e:
        logger.error(f"Failed to load config {file_path}: {e}. Returning default settings.")
        return fallback


def save_json_config(file_path: Union[str, Path], config: Dict[str, Any]) -> bool:
    """Saves a dictionary configuration to a JSON file.

    Args:
        file_path: Target path to the JSON file.
        config: Configuration dictionary to serialize.

    Returns:
        True if save was successful, False otherwise.
    """
    path = Path(file_path)
    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON config to {file_path}: {e}")
        return False
