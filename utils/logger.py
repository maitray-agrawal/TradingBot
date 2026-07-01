"""Centralized logging system for PrimeTrade AI.

Configures colored console logs alongside size-rotating log files routed based on
module context (analytics, bot, system, errors).
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Import path definitions
from config.paths import BOT_LOG_DIR, SYSTEM_LOG_DIR, ensure_directories_exist

# Size bounds for log rotation: 5 MB limit per file, maximum 3 backup files
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3

# Formatting string for standard files
FILE_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)


class ANSIColors:
    """Color codes for formatting terminal logs manually if rich is not running."""

    RESET = "\033[0m"
    DEBUG = "\033[36m"  # Cyan
    INFO = "\033[32m"  # Green
    WARNING = "\033[33m"  # Yellow
    ERROR = "\033[31m"  # Red
    CRITICAL = "\033[41m\033[37m"  # White text on red background


class ColorConsoleFormatter(logging.Formatter):
    """Console formatter mapping specific log levels to terminal colors."""

    def format(self, record: logging.LogRecord) -> str:
        # Save original levelname to restore it later
        orig_levelname = record.levelname
        color = ANSIColors.RESET

        if record.levelno == logging.DEBUG:
            color = ANSIColors.DEBUG
        elif record.levelno == logging.INFO:
            color = ANSIColors.INFO
        elif record.levelno == logging.WARNING:
            color = ANSIColors.WARNING
        elif record.levelno == logging.ERROR:
            color = ANSIColors.ERROR
        elif record.levelno == logging.CRITICAL:
            color = ANSIColors.CRITICAL

        # Format levelname with terminal colors
        record.levelname = f"{color}{orig_levelname:<8}{ANSIColors.RESET}"

        # Run base format
        result = super().format(record)

        # Restore original levelname
        record.levelname = orig_levelname
        return result


def setup_logging(level_name: str = "INFO") -> None:
    """Initializes and configures the logging hierarchy.

    Args:
        level_name: Standard log level name string (e.g. 'DEBUG', 'INFO').
    """
    # Ensure all directories exist before setting up file handlers
    ensure_directories_exist()

    log_level = getattr(logging, level_name.upper(), logging.INFO)

    # Clear existing handlers from root logger to prevent duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    # 1. Colored Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColorConsoleFormatter(
        fmt="%(asctime)s - %(name)-10s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 2. System Log File Handler (Root / system.log)
    system_log_path = SYSTEM_LOG_DIR / "system.log"
    system_handler = RotatingFileHandler(
        system_log_path,
        maxBytes=MAX_LOG_SIZE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    system_handler.setLevel(logging.DEBUG)  # Keep verbose system file log
    file_formatter = logging.Formatter(FILE_FORMAT)
    system_handler.setFormatter(file_formatter)
    root_logger.addHandler(system_handler)

    # 3. Global Error File Handler (Root / errors.log)
    error_log_path = SYSTEM_LOG_DIR / "errors.log"
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=MAX_LOG_SIZE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)  # ERROR and CRITICAL only
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)

    # 4. Analytics Specific Log File Handler
    analytics_logger = logging.getLogger("analytics")
    analytics_logger.setLevel(log_level)
    analytics_logger.propagate = (
        True  # Propagate to root for system.log, errors.log, and console
    )

    analytics_log_path = SYSTEM_LOG_DIR / "analytics.log"
    analytics_handler = RotatingFileHandler(
        analytics_log_path,
        maxBytes=MAX_LOG_SIZE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    analytics_handler.setLevel(log_level)
    analytics_handler.setFormatter(file_formatter)
    analytics_logger.addHandler(analytics_handler)

    # 5. Trading Bot Specific Log File Handler
    bot_logger = logging.getLogger("bot")
    bot_logger.setLevel(log_level)
    bot_logger.propagate = (
        True  # Propagate to root for system.log, errors.log, and console
    )

    bot_log_path = BOT_LOG_DIR / "bot.log"
    bot_handler = RotatingFileHandler(
        bot_log_path,
        maxBytes=MAX_LOG_SIZE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    bot_handler.setLevel(log_level)
    bot_handler.setFormatter(file_formatter)
    bot_logger.addHandler(bot_handler)

    logging.info("Logging infrastructure successfully configured.")
