"""
Unit tests for database module.

Tests database connection, schema creation, and CRUD operations.
"""

from __future__ import annotations

import pytest

from invoice_mcp_server.infrastructure.database import Database


class TestDatabase:
    """Tests for Database class."""

    @pytest.mark.asyncio
    async def test_connection(self, database: Database) -> None:
        """Test database connection."""
        assert database._connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self, config_with_temp_db) -> None:
        """Test database disconnection."""
        db = Database()
        await db.connect()
        assert db._connected is True

        await db.disconnect()
        assert db._connected is False

    @pytest.mark.asyncio
    async def test_execute_query(self, database: Database) -> None:
        """Test executing a query."""
        result = await database.execute("SELECT 1 as value")
        assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_one(self, database: Database) -> None:
        """Test fetching one row."""
        row = await database.fetch_one("SELECT 1 as value")
        assert row is not None
        assert row["value"] == 1

    @pytest.mark.asyncio
    async def test_fetch_all(self, database: Database) -> None:
        """Test fetching all rows."""
        rows = await database.fetch_all(
            "SELECT 1 as value UNION SELECT 2 as value"
        )
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_tables_created(self, database: Database) -> None:
        """Test that required tables are created."""
        tables = await database.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = [t["name"] for t in tables]

        assert "customers" in table_names
        assert "invoices" in table_names
        assert "line_items" in table_names

    @pytest.mark.asyncio
    async def test_singleton_pattern(self, config_with_temp_db) -> None:
        """Test database singleton pattern."""
        db1 = Database()
        db2 = Database()
        assert db1 is db2

    @pytest.mark.asyncio
    async def test_execute_with_parameters(self, database: Database) -> None:
        """Test executing query with parameters."""
        await database.execute(
            "INSERT INTO customers (id, name, email) VALUES (?, ?, ?)",
            ("test-id", "Test Name", "test@example.com"),
        )

        row = await database.fetch_one(
            "SELECT * FROM customers WHERE id = ?",
            ("test-id",),
        )
        assert row is not None
        assert row["name"] == "Test Name"
