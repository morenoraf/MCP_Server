"""
MCP Protocol definitions.

Defines the request/response structures for MCP communication
following the JSON-RPC 2.0 format used by MCP.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from datetime import datetime

from pydantic import BaseModel, Field


class MCPMethod(str, Enum):
    """MCP method types."""

    # Initialization
    INITIALIZE = "initialize"
    INITIALIZED = "notifications/initialized"

    # Tools
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"

    # Resources
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"

    # Prompts
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"

    # Notifications
    NOTIFICATION = "notification"


class MCPRequest(BaseModel):
    """
    MCP Request structure (JSON-RPC 2.0 format).

    Input Data:
        - jsonrpc: Protocol version (always "2.0")
        - method: The method to call
        - params: Optional parameters
        - id: Request ID for correlation
    """

    jsonrpc: str = Field(default="2.0")
    method: str = Field(...)
    params: dict[str, Any] | None = Field(default=None)
    id: int | str | None = Field(default=None)

    model_config = {"extra": "allow"}


class MCPResponse(BaseModel):
    """
    MCP Response structure (JSON-RPC 2.0 format).

    Output Data:
        - jsonrpc: Protocol version
        - result: Success result data
        - error: Error information if failed
        - id: Matching request ID
    """

    jsonrpc: str = Field(default="2.0")
    result: dict[str, Any] | None = Field(default=None)
    error: MCPError | None = Field(default=None)
    id: int | str | None = Field(default=None)

    @classmethod
    def success(cls, result: dict[str, Any], request_id: int | str | None = None) -> MCPResponse:
        """Create a success response."""
        return cls(result=result, id=request_id)

    @classmethod
    def error_response(
        cls,
        code: int,
        message: str,
        data: Any = None,
        request_id: int | str | None = None,
    ) -> MCPResponse:
        """Create an error response."""
        return cls(
            error=MCPError(code=code, message=message, data=data),
            id=request_id,
        )


class MCPError(BaseModel):
    """MCP Error structure."""

    code: int
    message: str
    data: Any | None = None


class ToolDefinition(BaseModel):
    """
    Tool definition with JSON Schema for parameters.

    Defines a tool that can modify system state.
    """

    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Human-readable description")
    inputSchema: dict[str, Any] = Field(
        ...,
        description="JSON Schema for tool parameters",
    )


class ResourceDefinition(BaseModel):
    """
    Resource definition for read-only data access.

    Resources provide data to the model without modifying state.
    """

    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Human-readable name")
    description: str | None = Field(default=None)
    mimeType: str | None = Field(default="application/json")


class PromptDefinition(BaseModel):
    """
    Prompt template definition.

    Prompts provide context and guidance to the model.
    """

    name: str = Field(..., description="Unique prompt identifier")
    description: str | None = Field(default=None)
    arguments: list[PromptArgument] | None = Field(default=None)


class PromptArgument(BaseModel):
    """Argument for a prompt template."""

    name: str
    description: str | None = None
    required: bool = False


class ToolResult(BaseModel):
    """Result from a tool call."""

    content: list[ContentItem] = Field(default_factory=list)
    isError: bool = False


class ContentItem(BaseModel):
    """Content item in a result."""

    type: str = "text"
    text: str | None = None
    data: str | None = None
    mimeType: str | None = None


class ServerCapabilities(BaseModel):
    """Server capability advertisement."""

    tools: dict[str, Any] | None = Field(default_factory=dict)
    resources: dict[str, Any] | None = Field(default_factory=dict)
    prompts: dict[str, Any] | None = Field(default_factory=dict)


class ServerInfo(BaseModel):
    """Server information."""

    name: str
    version: str


class InitializeResult(BaseModel):
    """Result of initialize request."""

    protocolVersion: str = "2024-11-05"
    capabilities: ServerCapabilities = Field(default_factory=ServerCapabilities)
    serverInfo: ServerInfo = Field(
        default_factory=lambda: ServerInfo(
            name="invoice-mcp-server",
            version="1.0.0",
        )
    )
