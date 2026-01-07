"""
MCP Resources module - Read-only data access.

Contains resource implementations for:
    - Static resources: Configuration, VAT rates
    - Dynamic resources: Customers, Invoices, Statistics
"""

__all__ = [
    "ConfigResource",
    "VATRatesResource",
    "CustomersListResource",
    "CustomerDetailResource",
    "InvoicesListResource",
    "InvoiceDetailResource",
    "RecentInvoicesResource",
    "OverdueInvoicesResource",
    "StatisticsResource",
    "get_all_resources",
]

from invoice_mcp_server.mcp.resources.static_resources import (
    ConfigResource,
    VATRatesResource,
)
from invoice_mcp_server.mcp.resources.dynamic_resources import (
    CustomersListResource,
    CustomerDetailResource,
    InvoicesListResource,
    InvoiceDetailResource,
    RecentInvoicesResource,
    OverdueInvoicesResource,
    StatisticsResource,
)


def get_all_resources():
    """Return list of all available resource classes."""
    return [
        ConfigResource,
        VATRatesResource,
        CustomersListResource,
        InvoicesListResource,
        RecentInvoicesResource,
        OverdueInvoicesResource,
        StatisticsResource,
    ]
