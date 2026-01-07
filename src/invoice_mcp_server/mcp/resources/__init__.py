"""
MCP Resources module - Read-only data access.

Contains resource implementations for:
    - Static resources: Configuration, VAT rates
    - Dynamic resources: Customers, Invoices, Statistics
    - Sync resources: Agent statuses, workspaces
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
from invoice_mcp_server.mcp.resources.sync_resources import get_sync_resources
from invoice_mcp_server.mcp.primitives import Resource


def get_all_resources() -> list[type[Resource]]:
    """Return list of all available resource classes."""
    resources = [
        ConfigResource,
        VATRatesResource,
        CustomersListResource,
        InvoicesListResource,
        RecentInvoicesResource,
        OverdueInvoicesResource,
        StatisticsResource,
    ]
    # Add multi-agent sync resources
    resources.extend(get_sync_resources())
    return resources
