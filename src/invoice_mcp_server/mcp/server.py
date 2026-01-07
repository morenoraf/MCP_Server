"""
Main MCP Server implementation.

The InvoiceMCPServer class is the central component that:
    - Registers all tools, resources, and prompts
    - Handles MCP protocol messages
    - Routes requests to appropriate handlers
"""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

from invoice_mcp_server.mcp.protocol import (
    MCPRequest,
    MCPResponse,
    MCPMethod,
    MCPError,
    ToolDefinition,
    ResourceDefinition,
    PromptDefinition,
    ToolResult,
    ContentItem,
    ServerCapabilities,
    ServerInfo,
    InitializeResult,
)
from invoice_mcp_server.mcp.primitives import Tool, Resource, Prompt
from invoice_mcp_server.infrastructure.database import Database
from invoice_mcp_server.infrastructure.repositories import (
    CustomerRepository,
    InvoiceRepository,
)
from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import MCPError as MCPException, ErrorCode

logger = get_logger(__name__)


class InvoiceMCPServer:
    """
    Main MCP Server for Invoice Management.

    Implements the Model Context Protocol server with:
        - Tools: Actions that modify state
        - Resources: Read-only data access
        - Prompts: Model guidance templates

    Setup Data (from config):
        - Server configuration
        - Database connection
        - Transport settings
    """

    def __init__(self) -> None:
        """Initialize the MCP server."""
        self._config = Config()
        self._database = Database()
        self._customer_repo: CustomerRepository | None = None
        self._invoice_repo: InvoiceRepository | None = None

        self._tools: dict[str, Tool] = {}
        self._resources: dict[str, Resource] = {}
        self._prompts: dict[str, Prompt] = {}

        self._initialized = False
        logger.info("InvoiceMCPServer instance created")

    async def initialize(self) -> None:
        """Initialize server and register all primitives."""
        if self._initialized:
            return

        # Connect to database
        await self._database.connect()

        # Initialize repositories
        self._customer_repo = CustomerRepository(self._database)
        self._invoice_repo = InvoiceRepository(self._database)

        # Register primitives
        self._register_tools()
        self._register_resources()
        self._register_prompts()

        self._initialized = True
        logger.info(
            f"MCP Server initialized with {len(self._tools)} tools, "
            f"{len(self._resources)} resources, {len(self._prompts)} prompts"
        )

    def _register_tools(self) -> None:
        """Register all available tools."""
        from invoice_mcp_server.mcp.tools import get_all_tools

        for tool_class in get_all_tools():
            tool = tool_class(self)
            self._tools[tool.name] = tool
            logger.debug(f"Registered tool: {tool.name}")

    def _register_resources(self) -> None:
        """Register all available resources."""
        from invoice_mcp_server.mcp.resources import get_all_resources

        for resource_class in get_all_resources():
            resource = resource_class(self)
            self._resources[resource.uri] = resource
            logger.debug(f"Registered resource: {resource.uri}")

    def _register_prompts(self) -> None:
        """Register all available prompts."""
        from invoice_mcp_server.mcp.prompts import get_all_prompts

        for prompt_class in get_all_prompts():
            prompt = prompt_class(self)
            self._prompts[prompt.name] = prompt
            logger.debug(f"Registered prompt: {prompt.name}")

    def get_customer_repository(self) -> CustomerRepository:
        """Get customer repository instance."""
        if not self._customer_repo:
            raise MCPException(
                "Server not initialized",
                code=ErrorCode.PROTOCOL_ERROR,
            )
        return self._customer_repo

    def get_invoice_repository(self) -> InvoiceRepository:
        """Get invoice repository instance."""
        if not self._invoice_repo:
            raise MCPException(
                "Server not initialized",
                code=ErrorCode.PROTOCOL_ERROR,
            )
        return self._invoice_repo

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """
        Handle an incoming MCP request.

        Routes the request to the appropriate handler based on method.
        """
        try:
            logger.debug(f"Handling request: {request.method}")

            if request.method == MCPMethod.INITIALIZE.value:
                return await self._handle_initialize(request)

            elif request.method == MCPMethod.TOOLS_LIST.value:
                return await self._handle_tools_list(request)

            elif request.method == MCPMethod.TOOLS_CALL.value:
                return await self._handle_tools_call(request)

            elif request.method == MCPMethod.RESOURCES_LIST.value:
                return await self._handle_resources_list(request)

            elif request.method == MCPMethod.RESOURCES_READ.value:
                return await self._handle_resources_read(request)

            elif request.method == MCPMethod.PROMPTS_LIST.value:
                return await self._handle_prompts_list(request)

            elif request.method == MCPMethod.PROMPTS_GET.value:
                return await self._handle_prompts_get(request)

            else:
                return MCPResponse.error_response(
                    code=-32601,
                    message=f"Method not found: {request.method}",
                    request_id=request.id,
                )

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return MCPResponse.error_response(
                code=-32603,
                message=str(e),
                request_id=request.id,
            )

    async def _handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle initialize request."""
        await self.initialize()

        result = InitializeResult(
            capabilities=ServerCapabilities(
                tools={"listChanged": True},
                resources={"subscribe": True, "listChanged": True},
                prompts={"listChanged": True},
            ),
            serverInfo=ServerInfo(
                name="invoice-mcp-server",
                version="1.0.0",
            ),
        )

        return MCPResponse.success(
            result=result.model_dump(),
            request_id=request.id,
        )

    async def _handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/list request."""
        tools = [tool.get_definition().model_dump() for tool in self._tools.values()]

        return MCPResponse.success(
            result={"tools": tools},
            request_id=request.id,
        )

    async def _handle_tools_call(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/call request."""
        params = request.params or {}
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if not tool_name:
            return MCPResponse.error_response(
                code=-32602,
                message="Missing tool name",
                request_id=request.id,
            )

        tool = self._tools.get(tool_name)
        if not tool:
            return MCPResponse.error_response(
                code=ErrorCode.TOOL_NOT_FOUND.value,
                message=f"Tool not found: {tool_name}",
                request_id=request.id,
            )

        try:
            result = await tool.execute(**tool_args)
            return MCPResponse.success(
                result=result.model_dump(),
                request_id=request.id,
            )
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return MCPResponse.success(
                result=ToolResult(
                    content=[ContentItem(type="text", text=f"Error: {e}")],
                    isError=True,
                ).model_dump(),
                request_id=request.id,
            )

    async def _handle_resources_list(self, request: MCPRequest) -> MCPResponse:
        """Handle resources/list request."""
        resources = [
            resource.get_definition().model_dump()
            for resource in self._resources.values()
        ]

        return MCPResponse.success(
            result={"resources": resources},
            request_id=request.id,
        )

    async def _handle_resources_read(self, request: MCPRequest) -> MCPResponse:
        """Handle resources/read request."""
        params = request.params or {}
        uri = params.get("uri")

        if not uri:
            return MCPResponse.error_response(
                code=-32602,
                message="Missing resource URI",
                request_id=request.id,
            )

        resource = self._resources.get(uri)
        if not resource:
            return MCPResponse.error_response(
                code=ErrorCode.RESOURCE_NOT_FOUND.value,
                message=f"Resource not found: {uri}",
                request_id=request.id,
            )

        try:
            data = await resource.read()
            return MCPResponse.success(
                result={
                    "contents": [{
                        "uri": uri,
                        "mimeType": resource.mime_type,
                        "text": json.dumps(data, indent=2, default=str),
                    }]
                },
                request_id=request.id,
            )
        except Exception as e:
            logger.error(f"Resource read failed: {uri} - {e}")
            return MCPResponse.error_response(
                code=-32603,
                message=str(e),
                request_id=request.id,
            )

    async def _handle_prompts_list(self, request: MCPRequest) -> MCPResponse:
        """Handle prompts/list request."""
        prompts = [
            prompt.get_definition().model_dump()
            for prompt in self._prompts.values()
        ]

        return MCPResponse.success(
            result={"prompts": prompts},
            request_id=request.id,
        )

    async def _handle_prompts_get(self, request: MCPRequest) -> MCPResponse:
        """Handle prompts/get request."""
        params = request.params or {}
        prompt_name = params.get("name")
        prompt_args = params.get("arguments", {})

        if not prompt_name:
            return MCPResponse.error_response(
                code=-32602,
                message="Missing prompt name",
                request_id=request.id,
            )

        prompt = self._prompts.get(prompt_name)
        if not prompt:
            return MCPResponse.error_response(
                code=-32602,
                message=f"Prompt not found: {prompt_name}",
                request_id=request.id,
            )

        try:
            messages = await prompt.get_messages(**prompt_args)
            return MCPResponse.success(
                result={
                    "description": prompt.description,
                    "messages": messages,
                },
                request_id=request.id,
            )
        except Exception as e:
            logger.error(f"Prompt generation failed: {prompt_name} - {e}")
            return MCPResponse.error_response(
                code=-32603,
                message=str(e),
                request_id=request.id,
            )

    async def shutdown(self) -> None:
        """Shutdown the server and cleanup resources."""
        logger.info("Shutting down MCP server...")
        await self._database.disconnect()
        self._initialized = False
        logger.info("MCP server shutdown complete")


async def run_server() -> None:
    """Run the MCP server (entry point)."""
    server = InvoiceMCPServer()
    await server.initialize()
    logger.info("Invoice MCP Server is ready")
