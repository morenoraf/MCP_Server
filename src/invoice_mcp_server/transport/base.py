"""
Base transport class - Abstract interface for all transports.

Defines the contract that all transport implementations must follow.
This enables swapping transports without changing business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invoice_mcp_server.mcp.server import InvoiceMCPServer
    from invoice_mcp_server.mcp.protocol import MCPRequest, MCPResponse


class Transport(ABC):
    """
    Abstract base class for transport implementations.

    All transports must implement:
        - start: Begin listening for connections
        - stop: Gracefully shutdown
        - send: Send a response
        - receive: Receive incoming requests

    The transport is responsible for:
        - Message framing/deframing
        - Connection management
        - Protocol-specific encoding
    """

    def __init__(self) -> None:
        """Initialize transport."""
        self._server: InvoiceMCPServer | None = None
        self._running = False

    def set_server(self, server: InvoiceMCPServer) -> None:
        """Set the MCP server instance."""
        self._server = server

    @property
    def is_running(self) -> bool:
        """Check if transport is running."""
        return self._running

    @abstractmethod
    async def start(self) -> None:
        """Start the transport and begin processing."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport gracefully."""
        pass

    @abstractmethod
    async def send(self, response: MCPResponse) -> None:
        """Send a response message."""
        pass

    @abstractmethod
    def receive(self) -> AsyncGenerator[MCPRequest, None]:
        """Receive incoming request messages."""
        ...

    async def run(self) -> None:
        """
        Main run loop - process requests until stopped.

        This is the default implementation that:
        1. Starts the transport
        2. Processes incoming requests
        3. Sends responses
        4. Handles errors gracefully
        """
        if not self._server:
            raise RuntimeError("Server not set. Call set_server() first.")

        await self.start()

        try:
            async for request in self.receive():
                try:
                    response = await self._server.handle_request(request)
                    await self.send(response)
                except Exception as e:
                    from invoice_mcp_server.mcp.protocol import MCPResponse
                    error_response = MCPResponse.error_response(
                        code=-32603,
                        message=str(e),
                        request_id=request.id if request else None,
                    )
                    await self.send(error_response)
        finally:
            await self.stop()
