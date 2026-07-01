"""Registry manager to track and inventory loaded and scanned datasets."""

import json
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from analytics.ingestion.metadata import DatasetMetadata
from config.paths import DATA_DIR
from utils.logger import get_logger

logger = get_logger("analytics")


class DatasetRegistry:
    """Manages inventories of loaded or discovered datasets."""

    def __init__(self, registry_file: Optional[str] = None) -> None:
        """Initializes the registry.

        Args:
            registry_file: Optional path to persist the registry JSON.
        """
        if registry_file is None:
            self.registry_file = os.path.join(DATA_DIR, "registry.json")
        else:
            self.registry_file = registry_file

        self.entries: Dict[str, Dict[str, Any]] = {}
        self.load()

    def register(
        self,
        name: str,
        file_path: str,
        dataset_type: str,
        metadata: DatasetMetadata,
    ) -> None:
        """Registers or updates a dataset entry.

        Args:
            name: Human-readable or unique name of the dataset.
            file_path: Source file path.
            dataset_type: Classified dataset type (e.g. TRADER_HISTORY, FEAR_GREED).
            metadata: Structured metadata stats.
        """
        # Convert metadata dataclass to dict
        meta_dict = asdict(metadata)

        self.entries[name] = {
            "name": name,
            "file_path": file_path,
            "dataset_type": dataset_type,
            "rows": meta_dict["rows"],
            "columns": meta_dict["columns"],
            "memory_usage_bytes": meta_dict["memory_usage_bytes"],
            "file_size_bytes": meta_dict["file_size_bytes"],
            "column_types": meta_dict["column_types"],
            "null_counts": meta_dict["null_counts"],
            "duplicate_count": meta_dict["duplicate_count"],
            "load_time_seconds": meta_dict["load_time_seconds"],
            "checksum": meta_dict["file_checksum"],
            "last_modified": meta_dict["last_modified"],
            "target_columns_found": meta_dict["target_columns_found"],
        }
        logger.info(f"Dataset '{name}' registered successfully. Type: {dataset_type}")
        self.save()

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a registered dataset's details by name.

        Args:
            name: The registered dataset name.

        Returns:
            Dict containing metadata and attributes, or None if not registered.
        """
        return self.entries.get(name)

    def list_datasets(self) -> List[Dict[str, Any]]:
        """Returns list of all registered dataset summaries.

        Returns:
            List of registered dataset records.
        """
        return list(self.entries.values())

    def remove(self, name: str) -> None:
        """Removes a dataset from the registry.

        Args:
            name: The registered dataset name.
        """
        if name in self.entries:
            del self.entries[name]
            logger.info(f"Removed '{name}' from registry.")
            self.save()

    def load(self) -> None:
        """Loads the registry catalog from disk if it exists."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r") as f:
                    self.entries = json.load(f)
                logger.debug(f"Loaded {len(self.entries)} entries from registry file.")
            except Exception as e:
                logger.warning(f"Could not load registry JSON: {e}. Starting fresh.")
                self.entries = {}
        else:
            self.entries = {}

    def save(self) -> None:
        """Saves the registry catalog to disk."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
            with open(self.registry_file, "w") as f:
                json.dump(self.entries, f, indent=4)
            logger.debug(f"Saved registry entries to {self.registry_file}")
        except Exception as e:
            logger.error(f"Failed to write registry JSON file: {e}")
