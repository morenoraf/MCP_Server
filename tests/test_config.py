"""
Unit tests for configuration module.

Tests configuration loading, defaults, and environment overrides.
"""

from __future__ import annotations

import os

import pytest

from invoice_mcp_server.shared.config import (
    Config,
    DatabaseConfig,
    ServerConfig,
    InvoiceConfig,
    LoggingConfig,
    TransportConfig,
)


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_default_values(self) -> None:
        """Test default database configuration values."""
        config = DatabaseConfig()
        assert config.pool_size == 5
        assert config.timeout == 30.0

    def test_env_override(self) -> None:
        """Test environment variable override."""
        os.environ["DB_POOL_SIZE"] = "10"
        os.environ["DB_TIMEOUT"] = "60.0"
        Config.reset()

        config = DatabaseConfig()
        assert config.pool_size == 10
        assert config.timeout == 60.0

        del os.environ["DB_POOL_SIZE"]
        del os.environ["DB_TIMEOUT"]


class TestServerConfig:
    """Tests for ServerConfig."""

    def test_default_values(self) -> None:
        """Test default server configuration values."""
        config = ServerConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8080
        assert config.debug is False

    def test_env_override(self) -> None:
        """Test environment variable override."""
        os.environ["SERVER_HOST"] = "0.0.0.0"
        os.environ["SERVER_PORT"] = "9000"
        os.environ["DEBUG"] = "true"
        Config.reset()

        config = ServerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.debug is True

        del os.environ["SERVER_HOST"]
        del os.environ["SERVER_PORT"]
        del os.environ["DEBUG"]


class TestInvoiceConfig:
    """Tests for InvoiceConfig."""

    def test_default_values(self) -> None:
        """Test default invoice configuration values."""
        config = InvoiceConfig()
        assert config.vat_rate == 0.17
        assert config.currency == "ILS"
        assert config.invoice_prefix == "INV"
        assert config.default_payment_terms == 30

    def test_env_override(self) -> None:
        """Test environment variable override."""
        os.environ["VAT_RATE"] = "0.20"
        os.environ["CURRENCY"] = "USD"
        Config.reset()

        config = InvoiceConfig()
        assert config.vat_rate == 0.20
        assert config.currency == "USD"

        del os.environ["VAT_RATE"]
        del os.environ["CURRENCY"]


class TestConfig:
    """Tests for main Config class."""

    def test_singleton_pattern(self) -> None:
        """Test that Config follows singleton pattern."""
        config1 = Config()
        config2 = Config()
        assert config1 is config2

    def test_reset(self) -> None:
        """Test configuration reset."""
        config1 = Config()
        Config.reset()
        config2 = Config()
        assert config1 is not config2

    def test_to_dict(self) -> None:
        """Test configuration export to dictionary."""
        config = Config()
        data = config.to_dict()

        assert "database" in data
        assert "server" in data
        assert "invoice" in data
        assert "logging" in data
        assert "transport" in data

    def test_all_sub_configs(self) -> None:
        """Test all sub-configurations are accessible."""
        config = Config()

        assert config.database is not None
        assert config.server is not None
        assert config.invoice is not None
        assert config.logging is not None
        assert config.transport is not None
