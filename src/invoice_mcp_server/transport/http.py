"""
HTTP/SSE Transport implementation.

Provides transport over HTTP with Server-Sent Events (SSE) support.
This enables web browsers and HTTP clients to communicate with the MCP server.

Features:
    - RESTful JSON-RPC endpoint
    - SSE for streaming responses
    - CORS support
    - Health check endpoint
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from invoice_mcp_server.transport.base import Transport
from invoice_mcp_server.mcp.protocol import MCPRequest, MCPResponse
from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import TransportError

logger = get_logger(__name__)


class HttpTransport(Transport):
    """
    HTTP/SSE transport for MCP communication.

    Provides a web server endpoint for MCP clients.

    Input Data:
        - HTTP POST requests with JSON-RPC body

    Output Data:
        - HTTP responses with JSON-RPC body
        - SSE events for notifications

    Setup Data (from config):
        - host: Server bind address
        - port: Server port
        - timeout: Request timeout
    """

    def __init__(self) -> None:
        """Initialize HTTP transport."""
        super().__init__()
        self._config = Config()
        self._app: Any = None  # aiohttp.web.Application
        self._site: Any = None  # aiohttp.web.TCPSite
        self._request_queue: asyncio.Queue[MCPRequest] = asyncio.Queue()
        self._pending_responses: dict[str | int, asyncio.Future[MCPResponse]] = {}

    async def start(self) -> None:
        """Start the HTTP server."""
        if self._running:
            return

        try:
            from aiohttp import web

            self._app = web.Application()
            self._setup_routes()

            runner = web.AppRunner(self._app)
            await runner.setup()

            self._site = web.TCPSite(
                runner,
                self._config.server.host,
                self._config.server.port,
            )
            await self._site.start()

            self._running = True
            logger.info(
                f"HTTP transport started on "
                f"http://{self._config.server.host}:{self._config.server.port}"
            )
        except ImportError:
            raise TransportError(
                message="aiohttp not installed. Install with: pip install aiohttp",
                transport_type="http",
            )
        except Exception as e:
            raise TransportError(
                message=f"Failed to start HTTP server: {e}",
                transport_type="http",
                cause=e if isinstance(e, Exception) else None,
            )

    def _setup_routes(self) -> None:
        """Set up HTTP routes."""
        self._app.router.add_post("/mcp", self._handle_mcp_request)
        self._app.router.add_get("/mcp/sse", self._handle_sse)
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_options("/mcp", self._handle_cors)

    async def _handle_mcp_request(self, request: Any) -> Any:
        """Handle incoming MCP request."""
        from aiohttp import web

        # CORS headers
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        try:
            data = await request.json()
            mcp_request = MCPRequest(**data)

            # Queue the request and wait for response
            response_future: asyncio.Future[MCPResponse] = asyncio.Future()
            request_id = mcp_request.id or id(mcp_request)
            self._pending_responses[request_id] = response_future

            await self._request_queue.put(mcp_request)

            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(
                    response_future,
                    timeout=self._config.transport.timeout,
                )
                return web.json_response(
                    response.model_dump(),
                    headers=headers,
                )
            except asyncio.TimeoutError:
                return web.json_response(
                    MCPResponse.error_response(
                        code=-32000,
                        message="Request timeout",
                        request_id=mcp_request.id,
                    ).model_dump(),
                    status=504,
                    headers=headers,
                )
            finally:
                self._pending_responses.pop(request_id, None)

        except json.JSONDecodeError:
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400,
                headers=headers,
            )
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return web.json_response(
                MCPResponse.error_response(
                    code=-32603,
                    message=str(e),
                ).model_dump(),
                status=500,
                headers=headers,
            )

    async def _handle_sse(self, request: Any) -> Any:
        """Handle SSE connection for streaming responses."""
        from aiohttp import web

        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )
        await response.prepare(request)

        try:
            while self._running:
                # Send heartbeat every 30 seconds
                await response.write(b": heartbeat\n\n")
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass
        finally:
            await response.write_eof()

        return response

    async def _handle_health(self, request: Any) -> Any:
        """Handle health check endpoint."""
        from aiohttp import web

        return web.json_response({
            "status": "healthy",
            "server": "invoice-mcp-server",
            "version": "1.0.0",
        })

    async def _handle_cors(self, request: Any) -> Any:
        """Handle CORS preflight requests."""
        from aiohttp import web

        return web.Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
        )

    async def stop(self) -> None:
        """Stop the HTTP server."""
        if not self._running:
            return

        logger.info("Stopping HTTP transport")
        self._running = False

        if self._site:
            await self._site.stop()

        logger.info("HTTP transport stopped")

    async def send(self, response: MCPResponse) -> None:
        """Send a response (resolves pending future)."""
        request_id = response.id
        if request_id in self._pending_responses:
            future = self._pending_responses[request_id]
            if not future.done():
                future.set_result(response)

    async def receive(self) -> AsyncGenerator[MCPRequest, None]:
        """Receive requests from the queue."""
        while self._running:
            try:
                request = await asyncio.wait_for(
                    self._request_queue.get(),
                    timeout=1.0,
                )
                yield request
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
