"""
MCP Tools module - Actions that modify system state.

Contains all tool implementations for:
    - Customer management
    - Invoice management
    - Payment processing
    - Multi-agent synchronization
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
    return tools
