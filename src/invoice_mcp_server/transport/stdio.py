"""
STDIO Transport implementation.

Provides transport over standard input/output streams.
This is the primary transport for CLI-based MCP clients.

Features:
    - Line-delimited JSON messages
    - Async read/write
    - Windows-compatible using threads
    - Graceful shutdown
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from queue import Queue, Empty
from typing import AsyncIterator

from invoice_mcp_server.transport.base import Transport
from invoice_mcp_server.mcp.protocol import MCPRequest, MCPResponse
from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import TransportError

logger = get_logger(__name__)


class StdioTransport(Transport):
    """
    Standard I/O transport for MCP communication.

    Messages are exchanged as newline-delimited JSON over stdin/stdout.
    Uses threading for Windows compatibility.

    Input Data:
        - stdin: JSON-RPC requests (one per line)

    Output Data:
        - stdout: JSON-RPC responses (one per line)

    Setup Data (from config):
        - buffer_size: Read buffer size
        - timeout: Read timeout
    """

    def __init__(self) -> None:
        """Initialize STDIO transport."""
        super().__init__()
        self._config = Config()
        self._input_queue: Queue[str | None] = Queue()
        self._read_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _read_stdin_thread(self) -> None:
        """Thread function to read from stdin."""
        try:
            while not self._stop_event.is_set():
                try:
                    line = sys.stdin.readline()
                    if not line:
                        # EOF
                        self._input_queue.put(None)
                        break
                    line = line.strip()
                    if line:
                        self._input_queue.put(line)
                except Exception as e:
                    logger.error(f"Error reading stdin: {e}")
                    break
        finally:
            self._input_queue.put(None)

    async def start(self) -> None:
        """Start the STDIO transport."""
        if self._running:
            return

        logger.info("Starting STDIO transport")

        # Start stdin reader thread
        self._stop_event.clear()
        self._read_thread = threading.Thread(
            target=self._read_stdin_thread,
            daemon=True,
        )
        self._read_thread.start()

        self._running = True
        logger.info("STDIO transport started")

    async def stop(self) -> None:
        """Stop the STDIO transport."""
        if not self._running:
            return

        logger.info("Stopping STDIO transport")
        self._running = False
        self._stop_event.set()

        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1.0)

        logger.info("STDIO transport stopped")

    async def send(self, response: MCPResponse) -> None:
        """Send a response via stdout."""
        try:
            message = response.model_dump_json()
            sys.stdout.write(message + "\n")
            sys.stdout.flush()
            logger.debug(f"Sent response: {response.id}")
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
            raise TransportError(
                message="Failed to send response",
                transport_type="stdio",
                cause=e if isinstance(e, Exception) else None,
            )

    async def receive(self) -> AsyncIterator[MCPRequest]:
        """Receive requests from stdin."""
        while self._running:
            try:
                # Non-blocking check with small timeout
                try:
                    line = self._input_queue.get(timeout=0.1)
                except Empty:
                    await asyncio.sleep(0.01)
                    continue

                if line is None:
                    logger.info("STDIO EOF received")
                    break

                try:
                    data = json.loads(line)
                    request = MCPRequest(**data)
                    logger.debug(f"Received request: {request.method}")
                    yield request
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received: {e}")
                except Exception as e:
                    logger.warning(f"Invalid request: {e}")

            except asyncio.CancelledError:
                logger.info("STDIO receive cancelled")
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                if self._running:
                    continue
                break


class StdioTransportSync:
    """
    Synchronous STDIO transport for simpler use cases.

    This provides a blocking interface for when async is not needed.
    """

    def __init__(self) -> None:
        """Initialize sync transport."""
        self._running = False

    def read_request(self) -> MCPRequest | None:
        """Read a single request from stdin."""
        try:
            line = sys.stdin.readline()
            if not line:
                return None

            line = line.strip()
            if not line:
                return None

            data = json.loads(line)
            return MCPRequest(**data)
        except Exception as e:
            logger.error(f"Error reading request: {e}")
            return None

    def write_response(self, response: MCPResponse) -> None:
        """Write a response to stdout."""
        try:
            message = response.model_dump_json()
            sys.stdout.write(message + "\n")
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error writing response: {e}")
