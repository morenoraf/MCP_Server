"""
Static resources - Configuration and reference data.

Static resources contain data that rarely changes, such as:
    - System configuration
    - VAT rates
    - Currency information
"""

from __future__ import annotations

from typing import Any

from invoice_mcp_server.mcp.primitives import StaticResource
from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger

logger = get_logger(__name__)


class ConfigResource(StaticResource):
    """
    System configuration resource.

    Provides read access to system configuration settings.
    Changes only when configuration is updated.
    """

    uri = "invoice://config/system"
    name = "System Configuration"
    description = "Current system configuration settings"

    async def read(self) -> dict[str, Any]:
        """Read system configuration."""
        config = Config()

        return {
            "type": "configuration",
            "data": {
                "invoice": {
                    "vat_rate": config.invoice.vat_rate,
                    "currency": config.invoice.currency,
                    "invoice_prefix": config.invoice.invoice_prefix,
                    "receipt_prefix": config.invoice.receipt_prefix,
                    "default_payment_terms": config.invoice.default_payment_terms,
                },
                "server": {
                    "host": config.server.host,
                    "port": config.server.port,
                },
            },
        }


class VATRatesResource(StaticResource):
    """
    VAT rates reference resource.

    Provides information about VAT rates.
    This is static data that changes only with tax law updates.
    """

    uri = "invoice://config/vat-rates"
    name = "VAT Rates"
    description = "Current VAT/tax rates information"

    async def read(self) -> dict[str, Any]:
        """Read VAT rates information."""
        config = Config()

        return {
            "type": "vat_rates",
            "data": {
                "current_rate": config.invoice.vat_rate,
                "rate_percent": f"{config.invoice.vat_rate * 100}%",
                "currency": config.invoice.currency,
                "rates": [
                    {
                        "name": "Standard VAT",
                        "rate": config.invoice.vat_rate,
                        "description": "Standard VAT rate for goods and services",
                    },
                    {
                        "name": "Zero Rate",
                        "rate": 0.0,
                        "description": "Zero-rated goods and services",
                    },
                ],
            },
        }


class CurrencyInfoResource(StaticResource):
    """
    Currency information resource.

    Provides information about supported currencies.
    """

    uri = "invoice://config/currency"
    name = "Currency Information"
    description = "Supported currency information"

    async def read(self) -> dict[str, Any]:
        """Read currency information."""
        config = Config()

        return {
            "type": "currency",
            "data": {
                "default_currency": config.invoice.currency,
                "currencies": [
                    {"code": "ILS", "name": "Israeli New Shekel", "symbol": "₪"},
                    {"code": "USD", "name": "US Dollar", "symbol": "$"},
                    {"code": "EUR", "name": "Euro", "symbol": "€"},
                    {"code": "GBP", "name": "British Pound", "symbol": "£"},
                ],
            },
        }
