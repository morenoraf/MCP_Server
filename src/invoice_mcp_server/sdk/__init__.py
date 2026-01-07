"""
SDK module for Invoice MCP Server.

Provides a high-level API for all invoice operations.
All GUI interfaces should use this SDK layer.
"""

from invoice_mcp_server.sdk.client import InvoiceSDK
from invoice_mcp_server.sdk.operations import (
    CustomerOperations,
    InvoiceOperations,
    ReportOperations,
)

__all__ = [
    "InvoiceSDK",
    "CustomerOperations",
    "InvoiceOperations",
    "ReportOperations",
]
