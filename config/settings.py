"""Configuration settings loader for PrimeTrade AI.

This module loads environment variables from .env and validates them against
Pydantic schemas, raising validation errors for incorrect types or configurations.
"""

import os
from typing import Any, Dict

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

from config.enums import Environment

# Load .env file if present
load_dotenv()


class SystemSettings(BaseModel):
    """Pydantic model representing validated system settings."""

    binance_api_key: str | None = Field(
        default=os.getenv("BINANCE_API_KEY"),
        description="Binance Testnet API Key.",
    )
    binance_secret_key: str | None = Field(
        default=os.getenv("BINANCE_SECRET_KEY"),
        description="Binance Testnet API Secret.",
    )
    testnet_url: str = Field(
        default=os.getenv("TESTNET_URL", "https://testnet.binancefuture.com"),
        description="Binance Futures Testnet API base URL.",
    )
    project_env: Environment = Field(
        default=Environment(os.getenv("PROJECT_ENV", "DEVELOPMENT").upper()),
        description="Current deployment environment (Development/Staging/Production).",
    )
    log_level: str = Field(
        default=os.getenv("LOG_LEVEL", "INFO").upper(),
        description="Console and file logger verbosity level.",
    )
    data_directory: str = Field(
        default=os.getenv("DATA_DIRECTORY", "data"),
        description="Relative or absolute path to the data storage folder.",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, val: str) -> str:
        """Validates that log level is a standard level."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_val = val.upper()
        if upper_val not in allowed_levels:
            raise ValueError(
                f"Invalid LOG_LEVEL '{val}'. Must be one of {allowed_levels}"
            )
        return upper_val

    @field_validator("testnet_url")
    @classmethod
    def validate_testnet_url(cls, val: str) -> str:
        """Validates that the testnet URL has a valid scheme."""
        if not (val.startswith("http://") or val.startswith("https://")):
            raise ValueError(
                f"Invalid TESTNET_URL '{val}'. Must start with http:// or https://"
            )
        return val


# Instantiate a singleton settings instance
settings = SystemSettings()
