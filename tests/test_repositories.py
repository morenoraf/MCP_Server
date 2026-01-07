"""
Unit tests for repository module.

Tests CRUD operations for customers and invoices.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from invoice_mcp_server.infrastructure.database import Database
from invoice_mcp_server.infrastructure.repositories import (
    CustomerRepository,
    InvoiceRepository,
)
from invoice_mcp_server.domain.models import Customer, Invoice, LineItem, InvoiceStatus


class TestCustomerRepository:
    """Tests for CustomerRepository."""

    @pytest.mark.asyncio
    async def test_create_customer(self, database: Database) -> None:
        """Test creating a customer."""
        repo = CustomerRepository(database)
        customer = Customer(
            id="cust-001",
            name="Test Customer",
            email="test@example.com",
        )

        result = await repo.create(customer)
        assert result.id == "cust-001"

    @pytest.mark.asyncio
    async def test_get_customer(self, database: Database) -> None:
        """Test getting a customer by ID."""
        repo = CustomerRepository(database)
        customer = Customer(
            id="cust-002",
            name="Test Customer",
            email="test2@example.com",
        )
        await repo.create(customer)

        result = await repo.get("cust-002")
        assert result is not None
        assert result.name == "Test Customer"

    @pytest.mark.asyncio
    async def test_get_nonexistent_customer(self, database: Database) -> None:
        """Test getting a nonexistent customer."""
        repo = CustomerRepository(database)
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_customers(self, database: Database) -> None:
        """Test listing all customers."""
        repo = CustomerRepository(database)

        for i in range(3):
            customer = Customer(
                id=f"list-cust-{i}",
                name=f"Customer {i}",
                email=f"customer{i}@example.com",
            )
            await repo.create(customer)

        customers = await repo.list_all()
        assert len(customers) >= 3

    @pytest.mark.asyncio
    async def test_update_customer(self, database: Database) -> None:
        """Test updating a customer."""
        repo = CustomerRepository(database)
        customer = Customer(
            id="update-cust",
            name="Original Name",
            email="original@example.com",
        )
        await repo.create(customer)

        customer.name = "Updated Name"
        await repo.update(customer)

        result = await repo.get("update-cust")
        assert result is not None
        assert result.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_customer(self, database: Database) -> None:
        """Test deleting a customer."""
        repo = CustomerRepository(database)
        customer = Customer(
            id="delete-cust",
            name="To Delete",
            email="delete@example.com",
        )
        await repo.create(customer)

        await repo.delete("delete-cust")
        result = await repo.get("delete-cust")
        assert result is None


class TestInvoiceRepository:
    """Tests for InvoiceRepository."""

    @pytest.mark.asyncio
    async def test_create_invoice(self, database: Database) -> None:
        """Test creating an invoice."""
        # First create a customer
        customer_repo = CustomerRepository(database)
        customer = Customer(
            id="inv-cust-001",
            name="Invoice Customer",
            email="invoice@example.com",
        )
        await customer_repo.create(customer)

        repo = InvoiceRepository(database)
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="inv-cust-001",
        )

        result = await repo.create(invoice)
        assert result.id == "inv-001"

    @pytest.mark.asyncio
    async def test_get_invoice(self, database: Database) -> None:
        """Test getting an invoice by ID."""
        customer_repo = CustomerRepository(database)
        customer = Customer(
            id="inv-cust-002",
            name="Customer",
            email="c2@example.com",
        )
        await customer_repo.create(customer)

        repo = InvoiceRepository(database)
        invoice = Invoice(
            id="inv-002",
            invoice_number="INV-000002",
            customer_id="inv-cust-002",
        )
        await repo.create(invoice)

        result = await repo.get("inv-002")
        assert result is not None
        assert result.invoice_number == "INV-000002"

    @pytest.mark.asyncio
    async def test_list_invoices(self, database: Database) -> None:
        """Test listing all invoices."""
        customer_repo = CustomerRepository(database)
        customer = Customer(
            id="list-inv-cust",
            name="Customer",
            email="list@example.com",
        )
        await customer_repo.create(customer)

        repo = InvoiceRepository(database)
        for i in range(3):
            invoice = Invoice(
                id=f"list-inv-{i}",
                invoice_number=f"INV-LIST-{i:06d}",
                customer_id="list-inv-cust",
            )
            await repo.create(invoice)

        invoices = await repo.list_all()
        assert len(invoices) >= 3

    @pytest.mark.asyncio
    async def test_add_line_item(self, database: Database) -> None:
        """Test adding a line item to invoice."""
        customer_repo = CustomerRepository(database)
        customer = Customer(
            id="item-cust",
            name="Customer",
            email="item@example.com",
        )
        await customer_repo.create(customer)

        repo = InvoiceRepository(database)
        invoice = Invoice(
            id="item-inv",
            invoice_number="INV-ITEM-001",
            customer_id="item-cust",
        )
        await repo.create(invoice)

        item = LineItem(
            description="Test Service",
            quantity=2,
            unit_price=Decimal("100.00"),
        )
        await repo.add_item("item-inv", item)

        result = await repo.get("item-inv")
        assert result is not None
        assert len(result.items) == 1
        assert result.items[0].description == "Test Service"

    @pytest.mark.asyncio
    async def test_update_status(self, database: Database) -> None:
        """Test updating invoice status."""
        customer_repo = CustomerRepository(database)
        customer = Customer(
            id="status-cust",
            name="Customer",
            email="status@example.com",
        )
        await customer_repo.create(customer)

        repo = InvoiceRepository(database)
        invoice = Invoice(
            id="status-inv",
            invoice_number="INV-STATUS-001",
            customer_id="status-cust",
        )
        await repo.create(invoice)

        await repo.update_status("status-inv", InvoiceStatus.SENT)

        result = await repo.get("status-inv")
        assert result is not None
        assert result.status == InvoiceStatus.SENT

    @pytest.mark.asyncio
    async def test_get_by_customer(self, database: Database) -> None:
        """Test getting invoices by customer."""
        customer_repo = CustomerRepository(database)
        customer = Customer(
            id="by-cust",
            name="Customer",
            email="bycust@example.com",
        )
        await customer_repo.create(customer)

        repo = InvoiceRepository(database)
        for i in range(2):
            invoice = Invoice(
                id=f"by-cust-inv-{i}",
                invoice_number=f"INV-BY-{i:06d}",
                customer_id="by-cust",
            )
            await repo.create(invoice)

        invoices = await repo.get_by_customer("by-cust")
        assert len(invoices) >= 2
