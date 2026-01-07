"""
Invoice MCP Server - Model Context Protocol Server for Invoice Management.

This package provides a complete MCP server implementation for managing invoices,
customers, and related business operations following the MCP architecture.

Architecture:
    - Stage 1: Infrastructure (config, logging, exceptions)
    - Stage 2: MCP Server with Tools
    - Stage 3: All Primitives (Tools, Resources, Prompts)
    - Stage 4: Transport Layer (STDIO, HTTP/SSE)
    - Stage 5: SDK and GUI (CLI, Web)
"""

__version__ = "1.0.0"
__author__ = "Student"
__all__ = [
    "__version__",
    "InvoiceMCPServer",
    "Config",
    "get_logger",
]

from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.mcp.server import InvoiceMCPServer
