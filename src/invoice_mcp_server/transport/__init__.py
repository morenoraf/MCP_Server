"""
Transport Layer module - Modular communication layer.

Provides multiple transport implementations:
    - STDIO: Standard input/output for CLI usage
    - HTTP/SSE: Web-based transport for browser/API access

The transport layer is completely decoupled from business logic,
allowing easy replacement without code changes.
"""

__all__ = [
    "Transport",
    "StdioTransport",
    "HttpTransport",
    "get_transport",
]

from invoice_mcp_server.transport.base import Transport
from invoice_mcp_server.transport.stdio import StdioTransport
from invoice_mcp_server.transport.http import HttpTransport


def get_transport(transport_type: str | None = None) -> Transport:
    """
    Factory function to get appropriate transport.

    Args:
        transport_type: Type of transport ('stdio' or 'http')
                       If None, reads from config

    Returns:
        Transport instance
    """
    from invoice_mcp_server.shared.config import Config

    if transport_type is None:
        config = Config()
        transport_type = config.transport.type

    if transport_type == "stdio":
        return StdioTransport()
    elif transport_type == "http":
        return HttpTransport()
    else:
        raise ValueError(f"Unknown transport type: {transport_type}")
