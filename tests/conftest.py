"""
Pytest configuration and fixtures.

Provides shared fixtures for all tests.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator

import pytest

from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import reset_logging
from invoice_mcp_server.infrastructure.database import Database


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_config() -> Generator[None, None, None]:
    """Reset configuration before each test."""
    Config.reset()
    reset_logging()
    yield
    Config.reset()
    reset_logging()


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def config_with_temp_db(temp_db_path: str) -> Config:
    """Create config with temporary database."""
    os.environ["DB_PATH"] = temp_db_path
    Config.reset()
    return Config()


@pytest.fixture
async def database(config_with_temp_db: Config) -> AsyncGenerator[Database, None]:
    """Create and connect database."""
    db = Database()
    await db.connect()
    yield db
    await db.disconnect()
