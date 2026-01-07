"""
MCP (Model Context Protocol) module.

Implements the three MCP primitives:
    - Tools: Actions that modify system state (Write)
    - Resources: Data reading operations (Read)
    - Prompts: Templates for model guidance

This module follows the MCP specification for AI agent communication.
"""

__all__ = [
    "InvoiceMCPServer",
    "Tool",
    "Resource",
    "Prompt",
    "MCPRequest",
    "MCPResponse",
]

from invoice_mcp_server.mcp.server import InvoiceMCPServer
from invoice_mcp_server.mcp.primitives import Tool, Resource, Prompt
from invoice_mcp_server.mcp.protocol import MCPRequest, MCPResponse
