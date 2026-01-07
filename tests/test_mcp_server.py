"""
Unit tests for MCP server module.

Tests server initialization, request handling, and method routing.
"""

from __future__ import annotations

import pytest

from invoice_mcp_server.mcp.server import InvoiceMCPServer
from invoice_mcp_server.mcp.protocol import MCPRequest, MCPMethod


class TestInvoiceMCPServer:
    """Tests for InvoiceMCPServer class."""

    @pytest.mark.asyncio
    async def test_initialization(self, config_with_temp_db) -> None:
        """Test server initialization."""
        server = InvoiceMCPServer()
        await server.initialize()

        assert server._initialized is True
        assert len(server._tools) > 0
        assert len(server._resources) > 0
        assert len(server._prompts) > 0

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_double_initialization(self, config_with_temp_db) -> None:
        """Test that double initialization is safe."""
        server = InvoiceMCPServer()
        await server.initialize()
        await server.initialize()  # Should not raise

        assert server._initialized is True
        await server.shutdown()

    @pytest.mark.asyncio
    async def test_handle_initialize(self, config_with_temp_db) -> None:
        """Test handling initialize request."""
        server = InvoiceMCPServer()

        request = MCPRequest(
            jsonrpc="2.0",
            id=1,
            method=MCPMethod.INITIALIZE.value,
            params={},
        )

        response = await server.handle_request(request)

        assert response.error is None
        assert response.result is not None
        assert "capabilities" in response.result
        assert "serverInfo" in response.result

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_handle_tools_list(self, config_with_temp_db) -> None:
        """Test handling tools/list request."""
        server = InvoiceMCPServer()
        await server.initialize()

        request = MCPRequest(
            jsonrpc="2.0",
            id=2,
            method=MCPMethod.TOOLS_LIST.value,
        )

        response = await server.handle_request(request)

        assert response.error is None
        assert "tools" in response.result
        assert len(response.result["tools"]) > 0

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_handle_resources_list(self, config_with_temp_db) -> None:
        """Test handling resources/list request."""
        server = InvoiceMCPServer()
        await server.initialize()

        request = MCPRequest(
            jsonrpc="2.0",
            id=3,
            method=MCPMethod.RESOURCES_LIST.value,
        )

        response = await server.handle_request(request)

        assert response.error is None
        assert "resources" in response.result

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_handle_prompts_list(self, config_with_temp_db) -> None:
        """Test handling prompts/list request."""
        server = InvoiceMCPServer()
        await server.initialize()

        request = MCPRequest(
            jsonrpc="2.0",
            id=4,
            method=MCPMethod.PROMPTS_LIST.value,
        )

        response = await server.handle_request(request)

        assert response.error is None
        assert "prompts" in response.result

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_handle_unknown_method(self, config_with_temp_db) -> None:
        """Test handling unknown method."""
        server = InvoiceMCPServer()
        await server.initialize()

        request = MCPRequest(
            jsonrpc="2.0",
            id=5,
            method="unknown/method",
        )

        response = await server.handle_request(request)

        assert response.error is not None
        assert response.error.code == -32601

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_handle_tools_call_missing_name(self, config_with_temp_db) -> None:
        """Test tools/call with missing tool name."""
        server = InvoiceMCPServer()
        await server.initialize()

        request = MCPRequest(
            jsonrpc="2.0",
            id=6,
            method=MCPMethod.TOOLS_CALL.value,
            params={},
        )

        response = await server.handle_request(request)

        assert response.error is not None
        assert response.error.code == -32602

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_handle_tools_call_unknown_tool(self, config_with_temp_db) -> None:
        """Test tools/call with unknown tool."""
        server = InvoiceMCPServer()
        await server.initialize()

        request = MCPRequest(
            jsonrpc="2.0",
            id=7,
            method=MCPMethod.TOOLS_CALL.value,
            params={"name": "unknown_tool"},
        )

        response = await server.handle_request(request)

        assert response.error is not None

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_handle_resources_read_missing_uri(self, config_with_temp_db) -> None:
        """Test resources/read with missing URI."""
        server = InvoiceMCPServer()
        await server.initialize()

        request = MCPRequest(
            jsonrpc="2.0",
            id=8,
            method=MCPMethod.RESOURCES_READ.value,
            params={},
        )

        response = await server.handle_request(request)

        assert response.error is not None
        assert response.error.code == -32602

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown(self, config_with_temp_db) -> None:
        """Test server shutdown."""
        server = InvoiceMCPServer()
        await server.initialize()
        await server.shutdown()

        assert server._initialized is False

    @pytest.mark.asyncio
    async def test_get_repositories(self, config_with_temp_db) -> None:
        """Test getting repository instances."""
        server = InvoiceMCPServer()
        await server.initialize()

        customer_repo = server.get_customer_repository()
        invoice_repo = server.get_invoice_repository()

        assert customer_repo is not None
        assert invoice_repo is not None

        await server.shutdown()
