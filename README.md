"""
Logging Module
Provides centralized logging with file rotation and console output
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from config.settings import LOGS_DIR, LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL, LOG_FILE_MAX_BYTES, LOG_BACKUP_COUNT


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Setup a logger with both file and console handlers

    Args:
        name: Logger name
        log_file: Optional specific log file name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    log_filename = log_file or f"{name}.log"
    file_path = LOGS_DIR / log_filename
    file_handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=LOG_FILE_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


class LoggerMixin:
    """Mixin class to add logging capability to any class"""

    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger
