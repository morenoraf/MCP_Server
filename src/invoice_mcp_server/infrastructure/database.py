"""
Database connection and management module.

Provides async SQLite database access with:
    - Connection pooling
    - Transaction management
    - Schema initialization
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import aiosqlite

from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import DatabaseError

logger = get_logger(__name__)


class Database:
    """
    Async SQLite database manager.

    Implements connection pooling and thread-safe operations.
    Uses the Singleton pattern for global access.
    """

    _instance: Database | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls) -> Database:
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize database manager."""
        if getattr(self, "_initialized", False):
            return

        self._config = Config()
        self._db_path = Path(self._config.database.path)
        self._connection: aiosqlite.Connection | None = None
        self._initialized = True

    async def connect(self) -> None:
        """Establish database connection and initialize schema."""
        async with Database._lock:
            if self._connection is not None:
                return

            # Ensure directory exists
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                self._connection = await aiosqlite.connect(
                    self._db_path,
                    timeout=self._config.database.timeout,
                )
                self._connection.row_factory = aiosqlite.Row
                await self._connection.execute("PRAGMA foreign_keys = ON")
                await self._initialize_schema()
                logger.info(f"Database connected: {self._db_path}")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise DatabaseError(
                    message="Failed to connect to database",
                    operation="connect",
                    cause=e if isinstance(e, Exception) else None,
                )

    async def disconnect(self) -> None:
        """Close database connection."""
        async with Database._lock:
            if self._connection:
                await self._connection.close()
                self._connection = None
                logger.info("Database disconnected")

    async def _initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        if not self._connection:
            raise DatabaseError("No database connection", operation="schema_init")

        schema = """
        -- Customers table
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            tax_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- Invoices table
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            invoice_number TEXT UNIQUE,
            customer_id TEXT NOT NULL,
            invoice_type TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            issue_date TEXT NOT NULL,
            due_date TEXT,
            vat_rate REAL NOT NULL,
            currency TEXT NOT NULL,
            paid_amount REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        -- Line items table
        CREATE TABLE IF NOT EXISTS line_items (
            id TEXT PRIMARY KEY,
            invoice_id TEXT NOT NULL,
            description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );

        -- Serial numbers table
        CREATE TABLE IF NOT EXISTS serial_numbers (
            id TEXT PRIMARY KEY,
            prefix TEXT NOT NULL,
            current_number INTEGER DEFAULT 0,
            year INTEGER NOT NULL,
            UNIQUE(prefix, year)
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id);
        CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
        CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(issue_date);
        CREATE INDEX IF NOT EXISTS idx_line_items_invoice ON line_items(invoice_id);
        """

        await self._connection.executescript(schema)
        await self._connection.commit()
        logger.debug("Database schema initialized")

    async def execute(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> aiosqlite.Cursor:
        """Execute a single query."""
        if not self._connection:
            await self.connect()

        try:
            if params:
                cursor = await self._connection.execute(query, params)
            else:
                cursor = await self._connection.execute(query)
            return cursor
        except Exception as e:
            logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
            raise DatabaseError(
                message="Query execution failed",
                operation="execute",
                cause=e if isinstance(e, Exception) else None,
            )

    async def execute_many(
        self,
        query: str,
        params_list: list[tuple[Any, ...]],
    ) -> None:
        """Execute a query with multiple parameter sets."""
        if not self._connection:
            await self.connect()

        try:
            await self._connection.executemany(query, params_list)
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise DatabaseError(
                message="Batch execution failed",
                operation="execute_many",
                cause=e if isinstance(e, Exception) else None,
            )

    async def commit(self) -> None:
        """Commit current transaction."""
        if self._connection:
            await self._connection.commit()

    async def rollback(self) -> None:
        """Rollback current transaction."""
        if self._connection:
            await self._connection.rollback()

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (for testing)."""
        cls._instance = None
