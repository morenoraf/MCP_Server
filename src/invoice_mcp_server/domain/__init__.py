"""
Domain module - Business entities and models.

Contains:
    - Customer model
    - Invoice model (Tax Invoice, Receipt, Transaction)
    - Line items
    - Serial number management
"""

__all__ = [
    "Customer",
    "Invoice",
    "InvoiceType",
    "InvoiceStatus",
    "LineItem",
    "SerialNumber",
]

from invoice_mcp_server.domain.models import (
    Customer,
    Invoice,
    InvoiceType,
    InvoiceStatus,
    LineItem,
    SerialNumber,
)
