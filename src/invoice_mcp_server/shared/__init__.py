"""
Shared module - Infrastructure layer containing configuration, logging, and exceptions.

This module provides:
    - Configuration management (no hardcoded values)
    - Logging infrastructure
    - Custom exceptions
    - Common utilities
"""

__all__ = [
    "Config",
    "get_logger",
    "InvoiceError",
    "ValidationError",
    "NotFoundError",
]

from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import (
    InvoiceError,
    ValidationError,
    NotFoundError,
)
