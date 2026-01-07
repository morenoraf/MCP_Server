"""
Configuration management module - No hardcoded values.

All configuration is loaded from environment variables or configuration files.
Follows the principle of zero hard-coded constants.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _get_project_root() -> Path:
    """Get the project root directory relative to this file."""
    return Path(__file__).parent.parent.parent.parent


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    path: str = field(default_factory=lambda: os.getenv(
        "DB_PATH",
        str(_get_project_root() / "data" / "invoices.db")
    ))
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "5")))
    timeout: float = field(default_factory=lambda: float(os.getenv("DB_TIMEOUT", "30.0")))


@dataclass
class ServerConfig:
    """Server configuration settings."""

    host: str = field(default_factory=lambda: os.getenv("SERVER_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("SERVER_PORT", "8080")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    workers: int = field(default_factory=lambda: int(os.getenv("WORKERS", "4")))


@dataclass
class InvoiceConfig:
    """Invoice-specific configuration."""

    vat_rate: float = field(default_factory=lambda: float(os.getenv("VAT_RATE", "0.17")))
    currency: str = field(default_factory=lambda: os.getenv("CURRENCY", "ILS"))
    invoice_prefix: str = field(default_factory=lambda: os.getenv("INVOICE_PREFIX", "INV"))
    receipt_prefix: str = field(default_factory=lambda: os.getenv("RECEIPT_PREFIX", "RCP"))
    default_payment_terms: int = field(default_factory=lambda: int(os.getenv("PAYMENT_TERMS", "30")))


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = field(default_factory=lambda: os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    file_path: str | None = field(default_factory=lambda: os.getenv("LOG_FILE"))
    max_bytes: int = field(default_factory=lambda: int(os.getenv("LOG_MAX_BYTES", "10485760")))
    backup_count: int = field(default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "5")))


@dataclass
class TransportConfig:
    """Transport layer configuration."""

    type: str = field(default_factory=lambda: os.getenv("TRANSPORT_TYPE", "stdio"))
    buffer_size: int = field(default_factory=lambda: int(os.getenv("TRANSPORT_BUFFER", "65536")))
    timeout: float = field(default_factory=lambda: float(os.getenv("TRANSPORT_TIMEOUT", "60.0")))


class Config:
    """
    Central configuration class - Singleton pattern.

    All values come from environment variables or .env files.
    No hardcoded constants in the application code.

    Usage:
        config = Config()
        vat_rate = config.invoice.vat_rate
    """

    _instance: Config | None = None
    _initialized: bool = False

    def __new__(cls) -> Config:
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize configuration from environment."""
        if Config._initialized:
            return

        # Load .env file if exists
        env_path = _get_project_root() / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        self.database = DatabaseConfig()
        self.server = ServerConfig()
        self.invoice = InvoiceConfig()
        self.logging = LoggingConfig()
        self.transport = TransportConfig()

        Config._initialized = True

    @classmethod
    def reset(cls) -> None:
        """Reset configuration (useful for testing)."""
        cls._instance = None
        cls._initialized = False

    def to_dict(self) -> dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "database": {
                "path": self.database.path,
                "pool_size": self.database.pool_size,
                "timeout": self.database.timeout,
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "debug": self.server.debug,
                "workers": self.server.workers,
            },
            "invoice": {
                "vat_rate": self.invoice.vat_rate,
                "currency": self.invoice.currency,
                "invoice_prefix": self.invoice.invoice_prefix,
                "receipt_prefix": self.invoice.receipt_prefix,
                "default_payment_terms": self.invoice.default_payment_terms,
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "file_path": self.logging.file_path,
            },
            "transport": {
                "type": self.transport.type,
                "buffer_size": self.transport.buffer_size,
                "timeout": self.transport.timeout,
            },
        }
