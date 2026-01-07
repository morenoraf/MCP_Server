"""
Main entry point for Invoice MCP Server.

Supports multiple modes:
    - stdio: Run as MCP server with stdio transport
    - http: Run as MCP server with HTTP transport
    - cli: Run CLI interface
    - web: Run web interface
"""

from __future__ import annotations

import asyncio
import sys

from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger

logger = get_logger(__name__)


async def run_stdio_server() -> None:
    """Run the MCP server with stdio transport."""
    from invoice_mcp_server.mcp.server import InvoiceMCPServer
    from invoice_mcp_server.transport.stdio import StdioTransport

    server = InvoiceMCPServer()
    transport = StdioTransport()

    await server.initialize()
    await transport.start()

    logger.info("MCP Server running with stdio transport")

    try:
        async for request in transport.receive():
            response = await server.handle_request(request)
            await transport.send(response)
    except KeyboardInterrupt:
        pass
    finally:
        await transport.stop()
        await server.shutdown()


async def run_http_server() -> None:
    """Run the MCP server with HTTP transport."""
    from invoice_mcp_server.mcp.server import InvoiceMCPServer
    from invoice_mcp_server.transport.http import HttpTransport

    server = InvoiceMCPServer()
    transport = HttpTransport()

    await server.initialize()
    await transport.start()

    logger.info("MCP Server running with HTTP transport")

    try:
        async for request in transport.receive():
            response = await server.handle_request(request)
            await transport.send(response)
    except KeyboardInterrupt:
        pass
    finally:
        await transport.stop()
        await server.shutdown()


def run_cli() -> None:
    """Run the CLI interface."""
    from invoice_mcp_server.gui.cli import cli_app
    # Remove the 'cli' argument from sys.argv so Click can parse the rest
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    cli_app()


def run_web() -> None:
    """Run the web interface."""
    import uvicorn
    from invoice_mcp_server.gui.web import create_web_app

    config = Config()
    app = create_web_app()

    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        log_level=config.logging.level.lower(),
    )


def main() -> None:
    """Main entry point with mode selection."""
    config = Config()
    mode = config.transport.type

    # Allow command-line override
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    # Handle help for CLI mode
    if mode == "cli":
        run_cli()
        return

    logger.info(f"Starting Invoice MCP Server in {mode} mode")

    if mode == "stdio":
        asyncio.run(run_stdio_server())
    elif mode == "http":
        asyncio.run(run_http_server())
    elif mode == "web":
        run_web()
    elif mode in ("--help", "-h"):
        print("Invoice MCP Server")
        print("")
        print("Usage: python -m invoice_mcp_server <mode> [options]")
        print("")
        print("Modes:")
        print("  stdio    Run MCP server with stdio transport")
        print("  http     Run MCP server with HTTP transport")
        print("  cli      Run CLI interface (use 'cli --help' for commands)")
        print("  web      Run web interface")
    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: stdio, http, cli, web")
        print("Use --help for more information")
        sys.exit(1)


if __name__ == "__main__":
    main()
