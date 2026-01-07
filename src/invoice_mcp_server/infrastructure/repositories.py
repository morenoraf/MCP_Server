"""
Repository classes for data persistence.

Implements the Repository pattern for:
    - Customer CRUD operations
    - Invoice CRUD operations
    - Serial number management
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from invoice_mcp_server.domain.models import (
    Customer,
    Invoice,
    InvoiceType,
    InvoiceStatus,
    LineItem,
    SerialNumber,
)
from invoice_mcp_server.infrastructure.database import Database
from invoice_mcp_server.infrastructure.lock_manager import LockManager
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import NotFoundError, DatabaseError

logger = get_logger(__name__)


class CustomerRepository:
    """
    Repository for Customer entity persistence.

    Provides CRUD operations with lock management for concurrent access.
    """

    def __init__(self, database: Database | None = None) -> None:
        """Initialize repository with database connection."""
        self._db = database or Database()
        self._lock_manager = LockManager()

    async def create(self, customer: Customer) -> Customer:
        """Create a new customer."""
        async with self._lock_manager.acquire(f"customer:{customer.id}"):
            await self._db.execute(
                """
                INSERT INTO customers (id, name, email, phone, address, tax_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    customer.id,
                    customer.name,
                    customer.email,
                    customer.phone,
                    customer.address,
                    customer.tax_id,
                    customer.created_at.isoformat(),
                    customer.updated_at.isoformat(),
                ),
            )
            await self._db.commit()
            logger.info(f"Customer created: {customer.id}")
            return customer

    async def get(self, customer_id: str) -> Customer:
        """Get a customer by ID."""
        cursor = await self._db.execute(
            "SELECT * FROM customers WHERE id = ?",
            (customer_id,),
        )
        row = await cursor.fetchone()

        if not row:
            raise NotFoundError("Customer", customer_id)

        return Customer(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            address=row["address"],
            tax_id=row["tax_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def update(self, customer: Customer) -> Customer:
        """Update an existing customer."""
        async with self._lock_manager.acquire(f"customer:{customer.id}"):
            customer.updated_at = datetime.utcnow()
            await self._db.execute(
                """
                UPDATE customers
                SET name = ?, email = ?, phone = ?, address = ?, tax_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    customer.name,
                    customer.email,
                    customer.phone,
                    customer.address,
                    customer.tax_id,
                    customer.updated_at.isoformat(),
                    customer.id,
                ),
            )
            await self._db.commit()
            logger.info(f"Customer updated: {customer.id}")
            return customer

    async def delete(self, customer_id: str) -> bool:
        """Delete a customer by ID."""
        async with self._lock_manager.acquire(f"customer:{customer_id}"):
            cursor = await self._db.execute(
                "DELETE FROM customers WHERE id = ?",
                (customer_id,),
            )
            await self._db.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Customer deleted: {customer_id}")
            return deleted

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Customer]:
        """List all customers with pagination."""
        cursor = await self._db.execute(
            "SELECT * FROM customers ORDER BY name LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()

        return [
            Customer(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                phone=row["phone"],
                address=row["address"],
                tax_id=row["tax_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    async def search(self, query: str) -> list[Customer]:
        """Search customers by name or email."""
        search_term = f"%{query}%"
        cursor = await self._db.execute(
            """
            SELECT * FROM customers
            WHERE name LIKE ? OR email LIKE ?
            ORDER BY name
            """,
            (search_term, search_term),
        )
        rows = await cursor.fetchall()

        return [
            Customer(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                phone=row["phone"],
                address=row["address"],
                tax_id=row["tax_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]


class InvoiceRepository:
    """
    Repository for Invoice entity persistence.

    Handles invoices and their line items with proper transaction management.
    """

    def __init__(self, database: Database | None = None) -> None:
        """Initialize repository with database connection."""
        self._db = database or Database()
        self._lock_manager = LockManager()

    async def _get_next_invoice_number(self, invoice_type: InvoiceType) -> str:
        """Generate the next invoice number for the given type."""
        from invoice_mcp_server.shared.config import Config
        config = Config()

        prefix = (
            config.invoice.invoice_prefix
            if invoice_type == InvoiceType.TAX_INVOICE
            else config.invoice.receipt_prefix
        )
        year = datetime.now().year

        async with self._lock_manager.acquire(f"serial:{prefix}:{year}"):
            cursor = await self._db.execute(
                "SELECT current_number FROM serial_numbers WHERE prefix = ? AND year = ?",
                (prefix, year),
            )
            row = await cursor.fetchone()

            if row:
                current = row["current_number"] + 1
                await self._db.execute(
                    "UPDATE serial_numbers SET current_number = ? WHERE prefix = ? AND year = ?",
                    (current, prefix, year),
                )
            else:
                current = 1
                await self._db.execute(
                    "INSERT INTO serial_numbers (id, prefix, current_number, year) VALUES (?, ?, ?, ?)",
                    (f"{prefix}-{year}", prefix, current, year),
                )

            await self._db.commit()
            return f"{prefix}-{year}-{current:06d}"

    async def create(self, invoice: Invoice) -> Invoice:
        """Create a new invoice with line items."""
        async with self._lock_manager.acquire(f"invoice:{invoice.id}"):
            # Generate invoice number if not set
            if not invoice.invoice_number:
                invoice.invoice_number = await self._get_next_invoice_number(
                    invoice.invoice_type
                )

            # Insert invoice
            await self._db.execute(
                """
                INSERT INTO invoices (
                    id, invoice_number, customer_id, invoice_type, status,
                    notes, issue_date, due_date, vat_rate, currency,
                    paid_amount, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice.id,
                    invoice.invoice_number,
                    invoice.customer_id,
                    invoice.invoice_type.value,
                    invoice.status.value,
                    invoice.notes,
                    invoice.issue_date.isoformat(),
                    invoice.due_date.isoformat() if invoice.due_date else None,
                    float(invoice.vat_rate),
                    invoice.currency,
                    float(invoice.paid_amount),
                    invoice.created_at.isoformat(),
                    invoice.updated_at.isoformat(),
                ),
            )

            # Insert line items
            for item in invoice.items:
                await self._db.execute(
                    """
                    INSERT INTO line_items (id, invoice_id, description, quantity, unit_price)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item.id,
                        invoice.id,
                        item.description,
                        float(item.quantity),
                        float(item.unit_price),
                    ),
                )

            await self._db.commit()
            logger.info(f"Invoice created: {invoice.invoice_number}")
            return invoice

    async def get(self, invoice_id: str) -> Invoice:
        """Get an invoice by ID with all line items."""
        cursor = await self._db.execute(
            "SELECT * FROM invoices WHERE id = ?",
            (invoice_id,),
        )
        row = await cursor.fetchone()

        if not row:
            raise NotFoundError("Invoice", invoice_id)

        # Get line items
        items_cursor = await self._db.execute(
            "SELECT * FROM line_items WHERE invoice_id = ?",
            (invoice_id,),
        )
        item_rows = await items_cursor.fetchall()

        items = [
            LineItem(
                id=item["id"],
                description=item["description"],
                quantity=Decimal(str(item["quantity"])),
                unit_price=Decimal(str(item["unit_price"])),
            )
            for item in item_rows
        ]

        return Invoice(
            id=row["id"],
            invoice_number=row["invoice_number"],
            customer_id=row["customer_id"],
            invoice_type=InvoiceType(row["invoice_type"]),
            status=InvoiceStatus(row["status"]),
            items=items,
            notes=row["notes"],
            issue_date=datetime.fromisoformat(row["issue_date"]).date(),
            due_date=(
                datetime.fromisoformat(row["due_date"]).date()
                if row["due_date"]
                else None
            ),
            vat_rate=Decimal(str(row["vat_rate"])),
            currency=row["currency"],
            paid_amount=Decimal(str(row["paid_amount"])),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def update(self, invoice: Invoice) -> Invoice:
        """Update an existing invoice."""
        async with self._lock_manager.acquire(f"invoice:{invoice.id}"):
            invoice.updated_at = datetime.utcnow()

            await self._db.execute(
                """
                UPDATE invoices
                SET status = ?, notes = ?, due_date = ?, paid_amount = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    invoice.status.value,
                    invoice.notes,
                    invoice.due_date.isoformat() if invoice.due_date else None,
                    float(invoice.paid_amount),
                    invoice.updated_at.isoformat(),
                    invoice.id,
                ),
            )

            # Update line items (delete and re-insert)
            await self._db.execute(
                "DELETE FROM line_items WHERE invoice_id = ?",
                (invoice.id,),
            )

            for item in invoice.items:
                await self._db.execute(
                    """
                    INSERT INTO line_items (id, invoice_id, description, quantity, unit_price)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item.id,
                        invoice.id,
                        item.description,
                        float(item.quantity),
                        float(item.unit_price),
                    ),
                )

            await self._db.commit()
            logger.info(f"Invoice updated: {invoice.invoice_number}")
            return invoice

    async def delete(self, invoice_id: str) -> bool:
        """Delete an invoice and its line items."""
        async with self._lock_manager.acquire(f"invoice:{invoice_id}"):
            cursor = await self._db.execute(
                "DELETE FROM invoices WHERE id = ?",
                (invoice_id,),
            )
            await self._db.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Invoice deleted: {invoice_id}")
            return deleted

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: InvoiceStatus | None = None,
        customer_id: str | None = None,
    ) -> list[Invoice]:
        """List invoices with filtering and pagination."""
        query = "SELECT * FROM invoices WHERE 1=1"
        params: list[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if customer_id:
            query += " AND customer_id = ?"
            params.append(customer_id)

        query += " ORDER BY issue_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await self._db.execute(query, tuple(params))
        rows = await cursor.fetchall()

        invoices = []
        for row in rows:
            # Get line items for each invoice
            items_cursor = await self._db.execute(
                "SELECT * FROM line_items WHERE invoice_id = ?",
                (row["id"],),
            )
            item_rows = await items_cursor.fetchall()

            items = [
                LineItem(
                    id=item["id"],
                    description=item["description"],
                    quantity=Decimal(str(item["quantity"])),
                    unit_price=Decimal(str(item["unit_price"])),
                )
                for item in item_rows
            ]

            invoices.append(
                Invoice(
                    id=row["id"],
                    invoice_number=row["invoice_number"],
                    customer_id=row["customer_id"],
                    invoice_type=InvoiceType(row["invoice_type"]),
                    status=InvoiceStatus(row["status"]),
                    items=items,
                    notes=row["notes"],
                    issue_date=datetime.fromisoformat(row["issue_date"]).date(),
                    due_date=(
                        datetime.fromisoformat(row["due_date"]).date()
                        if row["due_date"]
                        else None
                    ),
                    vat_rate=Decimal(str(row["vat_rate"])),
                    currency=row["currency"],
                    paid_amount=Decimal(str(row["paid_amount"])),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )

        return invoices

    async def get_recent(self, limit: int = 5) -> list[Invoice]:
        """Get most recent invoices."""
        return await self.list_all(limit=limit)

    async def get_by_customer(self, customer_id: str) -> list[Invoice]:
        """Get all invoices for a customer."""
        return await self.list_all(customer_id=customer_id)

    async def get_overdue(self) -> list[Invoice]:
        """Get all overdue invoices."""
        from datetime import date

        cursor = await self._db.execute(
            """
            SELECT * FROM invoices
            WHERE status NOT IN (?, ?, ?)
            AND due_date < ?
            ORDER BY due_date
            """,
            (
                InvoiceStatus.PAID.value,
                InvoiceStatus.CANCELLED.value,
                InvoiceStatus.OVERDUE.value,
                date.today().isoformat(),
            ),
        )
        rows = await cursor.fetchall()

        invoices = []
        for row in rows:
            items_cursor = await self._db.execute(
                "SELECT * FROM line_items WHERE invoice_id = ?",
                (row["id"],),
            )
            item_rows = await items_cursor.fetchall()

            items = [
                LineItem(
                    id=item["id"],
                    description=item["description"],
                    quantity=Decimal(str(item["quantity"])),
                    unit_price=Decimal(str(item["unit_price"])),
                )
                for item in item_rows
            ]

            invoices.append(
                Invoice(
                    id=row["id"],
                    invoice_number=row["invoice_number"],
                    customer_id=row["customer_id"],
                    invoice_type=InvoiceType(row["invoice_type"]),
                    status=InvoiceStatus(row["status"]),
                    items=items,
                    notes=row["notes"],
                    issue_date=datetime.fromisoformat(row["issue_date"]).date(),
                    due_date=(
                        datetime.fromisoformat(row["due_date"]).date()
                        if row["due_date"]
                        else None
                    ),
                    vat_rate=Decimal(str(row["vat_rate"])),
                    currency=row["currency"],
                    paid_amount=Decimal(str(row["paid_amount"])),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )

        return invoices
