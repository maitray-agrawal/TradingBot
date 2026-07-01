"""Upload handling utilities for saving and registering uploaded datasets."""

import os
from pathlib import Path
from typing import TYPE_CHECKING

from config.paths import UPLOADS_DATA_DIR
from utils.exceptions import ValidationError
from utils.logger import get_logger

if TYPE_CHECKING:
    from analytics.ingestion.loader import IngestionEngine
    from analytics.ingestion.metadata import Dataset

logger = get_logger("analytics")


class UploadHandler:
    """Manages dashboard file uploads, validates them, and registers them."""

    def __init__(self, engine: "IngestionEngine") -> None:
        """Initializes the upload handler.

        Args:
            engine: The IngestionEngine instance.
        """
        self.engine = engine
        # Ensure uploads folder exists
        os.makedirs(UPLOADS_DATA_DIR, exist_ok=True)

    def handle_upload(self, filename: str, content_bytes: bytes) -> "Dataset":
        """Saves file bytes to uploads directory, validates, registers, and returns the Dataset.

        Args:
            filename: Name of the uploaded file.
            content_bytes: Binary contents of the file.

        Returns:
            The loaded Dataset domain object.

        Raises:
            ValidationError: If the uploaded file name is empty or validation checks fail.
        """
        if not filename:
            raise ValidationError("Uploaded filename cannot be empty.")

        # Clean/sanitize filename
        clean_filename = Path(filename).name
        destination_path = UPLOADS_DATA_DIR / clean_filename

        logger.info(f"Saving uploaded file: {clean_filename} to {destination_path}")

        try:
            with open(destination_path, "wb") as f:
                f.write(content_bytes)
        except Exception as e:
            logger.error(f"Failed to write uploaded bytes to disk: {e}")
            raise ValidationError(f"Failed to write uploaded file to disk: {e}")

        # Now load the dataset using the main engine (which validates, registers, and profiles it)
        try:
            dataset = self.engine.load_dataset(str(destination_path), dataset_name=clean_filename)
            logger.info(f"Uploaded file {clean_filename} successfully processed and registered.")
            return dataset
        except Exception as e:
            # If ingestion/validation fails, clean up the file
            if destination_path.exists():
                try:
                    os.remove(destination_path)
                    logger.info(f"Cleaned up invalid uploaded file: {destination_path}")
                except Exception as cleanup_err:
                    logger.error(f"Failed to clean up invalid file: {cleanup_err}")
            raise e
