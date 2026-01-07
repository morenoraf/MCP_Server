"""
Unit tests for MCP protocol module.

Tests protocol message handling, serialization, and validation.
"""

from __future__ import annotations

import pytest

from invoice_mcp_server.mcp.protocol import (
    MCPRequest,
    MCPResponse,
    MCPMethod,
    MCPError,
    ToolDefinition,
    ResourceDefinition,
    PromptDefinition,
    ContentItem,
    ToolResult,
)


class TestMCPRequest:
    """Tests for MCPRequest model."""

    def test_valid_request(self) -> None:
        """Test creating valid request."""
        request = MCPRequest(
            jsonrpc="2.0",
            id=1,
            method="tools/list",
        )
        assert request.jsonrpc == "2.0"
        assert request.id == 1
        assert request.method == "tools/list"

    def test_request_with_params(self) -> None:
        """Test request with parameters."""
        request = MCPRequest(
            jsonrpc="2.0",
            id=2,
            method="tools/call",
            params={"name": "test_tool", "arguments": {"key": "value"}},
        )
        assert request.params["name"] == "test_tool"

    def test_request_without_id(self) -> None:
        """Test notification request (no ID)."""
        request = MCPRequest(
            jsonrpc="2.0",
            method="notifications/test",
        )
        assert request.id is None


class TestMCPResponse:
    """Tests for MCPResponse model."""

    def test_success_response(self) -> None:
        """Test creating success response."""
        response = MCPResponse.success(
            result={"data": "test"},
            request_id=1,
        )
        assert response.result == {"data": "test"}
        assert response.id == 1
        assert response.error is None

    def test_error_response(self) -> None:
        """Test creating error response."""
        response = MCPResponse.error_response(
            code=-32600,
            message="Invalid request",
            request_id=1,
        )
        assert response.error is not None
        assert response.error.code == -32600
        assert response.error.message == "Invalid request"
        assert response.result is None

    def test_response_serialization(self) -> None:
        """Test response serialization."""
        response = MCPResponse.success(
            result={"key": "value"},
            request_id=1,
        )
        data = response.model_dump()

        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert data["result"]["key"] == "value"


class TestMCPMethod:
    """Tests for MCPMethod enum."""

    def test_all_methods(self) -> None:
        """Test all method values."""
        methods = [m.value for m in MCPMethod]

        assert "initialize" in methods
        assert "tools/list" in methods
        assert "tools/call" in methods
        assert "resources/list" in methods
        assert "resources/read" in methods
        assert "prompts/list" in methods
        assert "prompts/get" in methods


class TestToolDefinition:
    """Tests for ToolDefinition model."""

    def test_basic_definition(self) -> None:
        """Test basic tool definition."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

    def test_with_input_schema(self) -> None:
        """Test tool with input schema."""
        schema = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
            },
            "required": ["param1"],
        }
        tool = ToolDefinition(
            name="test_tool",
            description="Test",
            inputSchema=schema,
        )
        assert tool.inputSchema == schema


class TestResourceDefinition:
    """Tests for ResourceDefinition model."""

    def test_basic_definition(self) -> None:
        """Test basic resource definition."""
        resource = ResourceDefinition(
            uri="test://resource",
            name="Test Resource",
            description="A test resource",
        )
        assert resource.uri == "test://resource"
        assert resource.name == "Test Resource"

    def test_with_mime_type(self) -> None:
        """Test resource with mime type."""
        resource = ResourceDefinition(
            uri="test://resource",
            name="Test",
            mimeType="application/json",
        )
        assert resource.mimeType == "application/json"


class TestPromptDefinition:
    """Tests for PromptDefinition model."""

    def test_basic_definition(self) -> None:
        """Test basic prompt definition."""
        prompt = PromptDefinition(
            name="test_prompt",
            description="A test prompt",
        )
        assert prompt.name == "test_prompt"

    def test_with_arguments(self) -> None:
        """Test prompt with arguments."""
        args = [
            {"name": "param1", "description": "First param", "required": True},
        ]
        prompt = PromptDefinition(
            name="test_prompt",
            description="Test",
            arguments=args,
        )
        assert len(prompt.arguments) == 1


class TestContentItem:
    """Tests for ContentItem model."""

    def test_text_content(self) -> None:
        """Test text content item."""
        item = ContentItem(type="text", text="Hello world")
        assert item.type == "text"
        assert item.text == "Hello world"

    def test_image_content(self) -> None:
        """Test image content item."""
        item = ContentItem(
            type="image",
            data="base64data",
            mimeType="image/png",
        )
        assert item.type == "image"
        assert item.data == "base64data"


class TestToolResult:
    """Tests for ToolResult model."""

    def test_success_result(self) -> None:
        """Test successful tool result."""
        result = ToolResult(
            content=[ContentItem(type="text", text="Success")],
        )
        assert result.isError is False
        assert len(result.content) == 1

    def test_error_result(self) -> None:
        """Test error tool result."""
        result = ToolResult(
            content=[ContentItem(type="text", text="Error occurred")],
            isError=True,
        )
        assert result.isError is True
