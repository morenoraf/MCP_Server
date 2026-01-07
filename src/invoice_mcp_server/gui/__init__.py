"""
GUI module for Invoice MCP Server.

Provides multiple interface types:
    - CLI: Command-line interface using Click
    - Web: Web interface using FastAPI
"""

from invoice_mcp_server.gui.cli import cli_app
from invoice_mcp_server.gui.web import create_web_app

__all__ = [
    "cli_app",
    "create_web_app",
]
