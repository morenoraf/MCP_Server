"""
SDK Client - Main entry point for all operations.

Provides a unified interface that all GUIs use to interact with the system.
All operations pass through this SDK layer.
"""

from __future__ import annotations

from typing import Any

from invoice_mcp_server.mcp.server import InvoiceMCPServer
from invoice_mcp_server.mcp.protocol import MCPRequest, MCPResponse
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.config import Config

logger = get_logger(__name__)


class InvoiceSDK:
    """
    Main SDK client for Invoice MCP Server.

    All operations are performed through this class.
    Provides both high-level methods and raw MCP request access.

    Usage:
        async with InvoiceSDK() as sdk:
            customers = await sdk.customers.list_all()
            invoice = await sdk.invoices.create(customer_id, items)
    """

    def __init__(self) -> None:
        """Initialize the SDK client."""
        self._config = Config()
        self._server = InvoiceMCPServer()
        self._initialized = False
        self._request_id = 0

        # Lazy-loaded operation modules
        self._customers: CustomerOperations | None = None
        self._invoices: InvoiceOperations | None = None
        self._reports: ReportOperations | None = None

        logger.info("InvoiceSDK client created")

    async def initialize(self) -> None:
        """Initialize the SDK and underlying server."""
        if self._initialized:
            return

        await self._server.initialize()
        self._initialized = True
        logger.info("InvoiceSDK initialized")

    async def shutdown(self) -> None:
        """Shutdown the SDK and cleanup resources."""
        if not self._initialized:
            return

        await self._server.shutdown()
        self._initialized = False
        logger.info("InvoiceSDK shutdown complete")

    async def __aenter__(self) -> InvoiceSDK:
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.shutdown()

    def _next_request_id(self) -> int:
        """Generate next request ID."""
        self._request_id += 1
        return self._request_id

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Call an MCP tool directly.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result as dictionary
        """
        request = MCPRequest(
            jsonrpc="2.0",
            id=self._next_request_id(),
            method="tools/call",
            params={"name": name, "arguments": arguments},
        )
        response = await self._server.handle_request(request)
        return response.result or {}

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """
        Read an MCP resource.

        Args:
            uri: Resource URI

        Returns:
            Resource data as dictionary
        """
        request = MCPRequest(
            jsonrpc="2.0",
            id=self._next_request_id(),
            method="resources/read",
            params={"uri": uri},
        )
        response = await self._server.handle_request(request)
        return response.result or {}

    @property
    def customers(self) -> CustomerOperations:
        """Get customer operations module."""
        if self._customers is None:
            from invoice_mcp_server.sdk.operations import CustomerOperations
            self._customers = CustomerOperations(self)
        return self._customers

    @property
    def invoices(self) -> InvoiceOperations:
        """Get invoice operations module."""
        if self._invoices is None:
            from invoice_mcp_server.sdk.operations import InvoiceOperations
            self._invoices = InvoiceOperations(self)
        return self._invoices

    @property
    def reports(self) -> ReportOperations:
        """Get report operations module."""
        if self._reports is None:
            from invoice_mcp_server.sdk.operations import ReportOperations
            self._reports = ReportOperations(self)
        return self._reports
