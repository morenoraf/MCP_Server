"""
MCP Tools module - Actions that modify system state.

Contains all tool implementations for:
    - Customer management
    - Invoice management
    - Payment processing
    - Multi-agent synchronization
    - Bulk operations
    - Export functionality
"""

__all__ = [
    "CreateCustomerTool",
    "UpdateCustomerTool",
    "DeleteCustomerTool",
    "CreateInvoiceTool",
    "AddInvoiceItemTool",
    "UpdateInvoiceStatusTool",
    "RecordPaymentTool",
    "SendInvoiceTool",
    "BulkCreateInvoicesTool",
    "BulkUpdateStatusTool",
    "BulkDeleteInvoicesTool",
    "ExportInvoicesCsvTool",
    "ExportInvoicesJsonTool",
    "ExportCustomerReportTool",
    "get_all_tools",
]

from invoice_mcp_server.mcp.tools.customer_tools import (
    CreateCustomerTool,
    UpdateCustomerTool,
    DeleteCustomerTool,
)
from invoice_mcp_server.mcp.tools.invoice_tools import (
    CreateInvoiceTool,
    AddInvoiceItemTool,
    UpdateInvoiceStatusTool,
    RecordPaymentTool,
    SendInvoiceTool,
)
from invoice_mcp_server.mcp.tools.sync_tools import get_sync_tools
from invoice_mcp_server.mcp.tools.bulk_tools import (
    BulkCreateInvoicesTool,
    BulkUpdateStatusTool,
    BulkDeleteInvoicesTool,
    get_bulk_tools,
)
from invoice_mcp_server.mcp.tools.export_tools import (
    ExportInvoicesCsvTool,
    ExportInvoicesJsonTool,
    ExportCustomerReportTool,
    get_export_tools,
)
from invoice_mcp_server.mcp.primitives import Tool


def get_all_tools() -> list[type[Tool]]:
    """Return list of all available tool classes."""
    tools = [
        CreateCustomerTool,
        UpdateCustomerTool,
        DeleteCustomerTool,
        CreateInvoiceTool,
        AddInvoiceItemTool,
        UpdateInvoiceStatusTool,
        RecordPaymentTool,
        SendInvoiceTool,
    ]
    # Add multi-agent sync tools
    tools.extend(get_sync_tools())
    # Add bulk operation tools
    tools.extend(get_bulk_tools())
    # Add export tools
    tools.extend(get_export_tools())
    return tools
