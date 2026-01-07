"""
Unit tests for database module.

Tests database connection, schema creation, and CRUD operations.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from invoice_mcp_server.infrastructure.database import Database


class TestDatabase:
    """Tests for Database class."""

    @pytest.mark.asyncio
    async def test_connection(self, database: Database) -> None:
        """Test database connection."""
        assert database._connection is not None

    @pytest.mark.asyncio
    async def test_disconnect(self, config_with_temp_db) -> None:
        """Test database disconnection."""
        db = Database()
        await db.connect()
        assert db._connection is not None

        await db.disconnect()
        assert db._connection is None

    @pytest.mark.asyncio
    async def test_execute_query(self, database: Database) -> None:
        """Test executing a query."""
        result = await database.execute("SELECT 1 as value")
        assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_one(self, database: Database) -> None:
        """Test fetching one row."""
        cursor = await database.execute("SELECT 1 as value")
        row = await cursor.fetchone()
        assert row is not None
        assert row["value"] == 1

    @pytest.mark.asyncio
    async def test_fetch_all(self, database: Database) -> None:
        """Test fetching all rows."""
        cursor = await database.execute(
            "SELECT 1 as value UNION SELECT 2 as value"
        )
        rows = await cursor.fetchall()
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_tables_created(self, database: Database) -> None:
        """Test that required tables are created."""
        cursor = await database.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        rows = await cursor.fetchall()
        table_names = [t["name"] for t in rows]

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
        now = datetime.utcnow().isoformat()
        await database.execute(
            "INSERT INTO customers (id, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            ("test-id", "Test Name", "test@example.com", now, now),
        )
        await database.commit()

        cursor = await database.execute(
            "SELECT * FROM customers WHERE id = ?",
            ("test-id",),
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["name"] == "Test Name"
