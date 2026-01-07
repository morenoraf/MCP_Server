"""
MCP Primitives - Tools, Resources, and Prompts.

This module defines the base classes for MCP primitives:
    - Tool: Actions that modify state (Write operations)
    - Resource: Data access (Read operations) - static and dynamic
    - Prompt: Templates for model guidance
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING


from invoice_mcp_server.mcp.protocol import (
    ToolDefinition,
    ResourceDefinition,
    PromptDefinition,
    ToolResult,
    ContentItem,
)
from invoice_mcp_server.shared.logging import get_logger

if TYPE_CHECKING:
    from invoice_mcp_server.mcp.server import InvoiceMCPServer

logger = get_logger(__name__)


class Tool(ABC):
    """
    Base class for MCP Tools.

    Tools perform actions that modify system state (Write operations).
    Each tool must define:
        - name: Unique identifier
        - description: What the tool does
        - input_schema: JSON Schema for parameters
        - execute: The action to perform

    Example:
        class CreateCustomerTool(Tool):
            name = "create_customer"
            description = "Create a new customer"
            ...
    """

    name: str
    description: str

    def __init__(self, server: InvoiceMCPServer) -> None:
        """Initialize tool with server reference."""
        self.server = server

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """Return JSON Schema for tool parameters."""
        pass

    @abstractmethod
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for listing."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema,
        )

    def _success_result(self, text: str) -> ToolResult:
        """Create a success result."""
        return ToolResult(
            content=[ContentItem(type="text", text=text)],
            isError=False,
        )

    def _error_result(self, message: str) -> ToolResult:
        """Create an error result."""
        return ToolResult(
            content=[ContentItem(type="text", text=f"Error: {message}")],
            isError=True,
        )

    def _json_result(self, data: dict[str, Any]) -> ToolResult:
        """Create a JSON result."""
        import json
        return ToolResult(
            content=[ContentItem(
                type="text",
                text=json.dumps(data, indent=2, default=str),
            )],
            isError=False,
        )


class Resource(ABC):
    """
    Base class for MCP Resources.

    Resources provide read-only data access. They can be:
        - Static: Configuration, constants (rarely change)
        - Dynamic: Live data that updates frequently

    Each resource has a URI for identification.
    """

    uri: str
    name: str
    description: str | None = None
    mime_type: str = "application/json"

    def __init__(self, server: InvoiceMCPServer) -> None:
        """Initialize resource with server reference."""
        self.server = server

    @abstractmethod
    async def read(self) -> dict[str, Any]:
        """Read the resource data."""
        pass

    def get_definition(self) -> ResourceDefinition:
        """Get resource definition for listing."""
        return ResourceDefinition(
            uri=self.uri,
            name=self.name,
            description=self.description,
            mimeType=self.mime_type,
        )


class StaticResource(Resource):
    """
    Static resource - configuration or reference data.

    Static resources change infrequently (e.g., VAT rates, currency info).
    """

    @property
    def is_dynamic(self) -> bool:
        """Static resources are not dynamic."""
        return False


class DynamicResource(Resource):
    """
    Dynamic resource - live data.

    Dynamic resources update frequently (e.g., recent invoices, statistics).
    """

    @property
    def is_dynamic(self) -> bool:
        """Dynamic resources are dynamic."""
        return True


class Prompt(ABC):
    """
    Base class for MCP Prompts.

    Prompts provide context and guidance to the model.
    They combine a system prompt with dynamic arguments.
    """

    name: str
    description: str | None = None

    def __init__(self, server: InvoiceMCPServer) -> None:
        """Initialize prompt with server reference."""
        self.server = server

    @property
    @abstractmethod
    def arguments(self) -> list[dict[str, Any]]:
        """Define prompt arguments."""
        pass

    @abstractmethod
    async def get_messages(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Generate prompt messages with given arguments."""
        pass

    def get_definition(self) -> PromptDefinition:
        """Get prompt definition for listing."""
        from invoice_mcp_server.mcp.protocol import PromptArgument

        return PromptDefinition(
            name=self.name,
            description=self.description,
            arguments=[
                PromptArgument(**arg) for arg in self.arguments
            ] if self.arguments else None,
        )
