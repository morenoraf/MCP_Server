"""
Logging infrastructure module.

Provides centralized logging configuration with support for:
    - Console output
    - File output with rotation
    - Structured logging
    - Different log levels per module
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invoice_mcp_server.shared.config import Config


_loggers: dict[str, logging.Logger] = {}
_configured: bool = False


def _configure_logging(config: Config | None = None) -> None:
    """Configure the logging system based on configuration."""
    global _configured

    if _configured:
        return

    if config is None:
        from invoice_mcp_server.shared.config import Config
        config = Config()

    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.logging.level.upper()))

    # Create formatter
    formatter = logging.Formatter(config.logging.format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, config.logging.level.upper()))
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if config.logging.file_path:
        log_path = Path(config.logging.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=config.logging.max_bytes,
            backupCount=config.logging.backup_count,
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, config.logging.level.upper()))
        root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str, config: Config | None = None) -> logging.Logger:
    """
    Get or create a logger with the given name.

    Args:
        name: Logger name (typically __name__ of the module)
        config: Optional configuration override

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing invoice", extra={"invoice_id": "INV-001"})
    """
    if name in _loggers:
        return _loggers[name]

    _configure_logging(config)

    logger = logging.getLogger(name)
    _loggers[name] = logger

    return logger


def reset_logging() -> None:
    """Reset logging configuration (useful for testing)."""
    global _configured, _loggers

    # Remove all handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    _loggers.clear()
    _configured = False


class LogContext:
    """
    Context manager for structured logging with extra context.

    Example:
        with LogContext(logger, invoice_id="INV-001", customer="ACME"):
            logger.info("Processing invoice")  # Includes context
    """

    def __init__(self, logger: logging.Logger, **context: str | int | float) -> None:
        """Initialize with logger and context values."""
        self.logger = logger
        self.context = context
        self._old_factory: logging.Callable[..., logging.LogRecord] | None = None

    def __enter__(self) -> LogContext:
        """Enter context and set up record factory."""
        old_factory = logging.getLogRecordFactory()
        self._old_factory = old_factory

        def record_factory(
            *args: object,
            **kwargs: object,
        ) -> logging.LogRecord:
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context and restore factory."""
        if self._old_factory:
            logging.setLogRecordFactory(self._old_factory)
