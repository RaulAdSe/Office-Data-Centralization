"""
Logging configuration for the CYPE scraper system.

Provides structured logging with file and console output.

Usage:
    from scraper.logging_config import setup_logging, get_logger

    setup_logging(level="INFO", log_file="scraper.log")
    logger = get_logger(__name__)

    logger.info("Starting extraction")
    logger.error("Extraction failed", extra={"url": url, "error": str(e)})
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Custom formatter with structured output
class StructuredFormatter(logging.Formatter):
    """Formatter that includes structured context fields."""

    def format(self, record):
        # Add timestamp
        record.timestamp = datetime.now().isoformat()

        # Format message
        message = super().format(record)

        # Add extra fields if present
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in (
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'message', 'timestamp'
            ) and not k.startswith('_')
        }

        if extra_fields:
            extras = ' | '.join(f'{k}={v}' for k, v in extra_fields.items())
            message = f"{message} | {extras}"

        return message


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
) -> None:
    """
    Configure logging for the scraper system.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file name (will be placed in log_dir)
        log_dir: Directory for log files
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_format = StructuredFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler (if requested)
    if log_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        file_path = log_path / log_file
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_format = StructuredFormatter(
            '%(timestamp)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class ProgressLogger:
    """
    Helper class for logging progress of batch operations.

    Usage:
        progress = ProgressLogger("Extracting", total=100, log_every=10)
        for url in urls:
            progress.update()
            # do work...
        progress.finish()
    """

    def __init__(
        self,
        operation: str,
        total: int,
        log_every: int = 10,
        logger: Optional[logging.Logger] = None
    ):
        self.operation = operation
        self.total = total
        self.log_every = log_every
        self.logger = logger or logging.getLogger(__name__)
        self.current = 0
        self.start_time = datetime.now()

    def update(self, increment: int = 1) -> None:
        """Update progress counter and log if needed."""
        self.current += increment

        if self.current % self.log_every == 0 or self.current == self.total:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = self.current / elapsed if elapsed > 0 else 0
            eta = (self.total - self.current) / rate if rate > 0 else 0

            self.logger.info(
                f"{self.operation}: {self.current}/{self.total} "
                f"({100*self.current/self.total:.1f}%) "
                f"[{rate:.1f}/s, ETA: {eta:.0f}s]"
            )

    def finish(self) -> None:
        """Log completion message."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.logger.info(
            f"{self.operation} complete: {self.current} items in {elapsed:.1f}s"
        )
