"""
MCP Prompts module - Templates for model guidance.

Contains prompt implementations for:
    - Invoice creation guidance
    - Customer management
    - Payment processing
    - Report generation
"""

__all__ = [
    "CreateInvoicePrompt",
    "ManageCustomerPrompt",
    "ProcessPaymentPrompt",
    "GenerateReportPrompt",
    "get_all_prompts",
]

from invoice_mcp_server.mcp.prompts.prompts import (
    CreateInvoicePrompt,
    ManageCustomerPrompt,
    ProcessPaymentPrompt,
    GenerateReportPrompt,
)
from invoice_mcp_server.mcp.primitives import Prompt


def get_all_prompts() -> list[type[Prompt]]:
    """Return list of all available prompt classes."""
    return [
        CreateInvoicePrompt,
        ManageCustomerPrompt,
        ProcessPaymentPrompt,
        GenerateReportPrompt,
    ]
