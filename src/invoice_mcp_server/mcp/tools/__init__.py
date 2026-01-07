"""
MCP Tools module - Actions that modify system state.

Contains all tool implementations for:
    - Customer management
    - Invoice management
    - Payment processing
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


def get_all_tools():
    """Return list of all available tool classes."""
    return [
        CreateCustomerTool,
        UpdateCustomerTool,
        DeleteCustomerTool,
        CreateInvoiceTool,
        AddInvoiceItemTool,
        UpdateInvoiceStatusTool,
        RecordPaymentTool,
        SendInvoiceTool,
    ]
