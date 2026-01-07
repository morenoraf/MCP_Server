"""
Unit tests for domain models.

Tests model validation, serialization, and business logic.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from invoice_mcp_server.domain.models import (
    Customer,
    LineItem,
    Invoice,
    InvoiceStatus,
    SerialNumber,
)


class TestSerialNumber:
    """Tests for SerialNumber model."""

    def test_create_serial(self) -> None:
        """Test serial number creation."""
        serial = SerialNumber(prefix="INV")
        assert serial.prefix == "INV"
        assert serial.current_number == 0
        assert serial.year == datetime.now().year

    def test_next_number(self) -> None:
        """Test generating next serial number."""
        serial = SerialNumber(prefix="INV", current_number=41)
        next_num = serial.next_number()
        assert next_num == f"INV-{datetime.now().year}-000042"
        assert serial.current_number == 42

    def test_sequential_generation(self) -> None:
        """Test sequential number generation."""
        serial = SerialNumber(prefix="REC")
        num1 = serial.next_number()
        num2 = serial.next_number()
        assert num1.endswith("-000001")
        assert num2.endswith("-000002")


class TestCustomer:
    """Tests for Customer model."""

    def test_valid_customer(self) -> None:
        """Test creating valid customer."""
        customer = Customer(
            id="CUST-001",
            name="Test Company",
            email="test@example.com",
        )
        assert customer.id == "CUST-001"
        assert customer.name == "Test Company"
        assert customer.email == "test@example.com"

    def test_customer_with_all_fields(self) -> None:
        """Test customer with all optional fields."""
        customer = Customer(
            id="CUST-001",
            name="Test Company",
            email="test@example.com",
            address="123 Main St",
            phone="123-456-7890",
        )
        assert customer.address == "123 Main St"
        assert customer.phone == "123-456-7890"

    def test_invalid_email(self) -> None:
        """Test customer with invalid email."""
        with pytest.raises(ValidationError):
            Customer(
                id="CUST-001",
                name="Test",
                email="not-an-email",
            )

    def test_empty_name(self) -> None:
        """Test customer with empty name."""
        with pytest.raises(ValidationError):
            Customer(
                id="CUST-001",
                name="",
                email="test@example.com",
            )

    def test_created_at_auto(self) -> None:
        """Test automatic created_at timestamp."""
        customer = Customer(
            id="CUST-001",
            name="Test",
            email="test@example.com",
        )
        assert customer.created_at is not None


class TestLineItem:
    """Tests for LineItem model."""

    def test_valid_line_item(self) -> None:
        """Test creating valid line item."""
        item = LineItem(
            description="Service",
            quantity=2,
            unit_price=Decimal("100.00"),
        )
        assert item.description == "Service"
        assert item.quantity == 2
        assert item.unit_price == Decimal("100.00")

    def test_line_total_calculation(self) -> None:
        """Test line_total calculation."""
        item = LineItem(
            description="Service",
            quantity=3,
            unit_price=Decimal("50.00"),
        )
        assert item.line_total == Decimal("150.00")

    def test_negative_quantity(self) -> None:
        """Test negative quantity validation."""
        with pytest.raises(ValidationError):
            LineItem(
                description="Service",
                quantity=-1,
                unit_price=Decimal("100.00"),
            )

    def test_negative_price(self) -> None:
        """Test negative price validation."""
        with pytest.raises(ValidationError):
            LineItem(
                description="Service",
                quantity=1,
                unit_price=Decimal("-100.00"),
            )

    def test_empty_description(self) -> None:
        """Test empty description validation."""
        with pytest.raises(ValidationError):
            LineItem(
                description="",
                quantity=1,
                unit_price=Decimal("100.00"),
            )


class TestInvoice:
    """Tests for Invoice model."""

    def test_valid_invoice(self) -> None:
        """Test creating valid invoice."""
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="CUST-001",
        )
        assert invoice.id == "inv-001"
        assert invoice.status == InvoiceStatus.DRAFT

    def test_invoice_with_items(self) -> None:
        """Test invoice with line items."""
        items = [
            LineItem(description="Item 1", quantity=2, unit_price=Decimal("100.00")),
            LineItem(description="Item 2", quantity=1, unit_price=Decimal("50.00")),
        ]
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="CUST-001",
            items=items,
        )
        assert len(invoice.items) == 2

    def test_subtotal_calculation(self) -> None:
        """Test subtotal calculation."""
        items = [
            LineItem(description="Item 1", quantity=2, unit_price=Decimal("100.00")),
            LineItem(description="Item 2", quantity=1, unit_price=Decimal("50.00")),
        ]
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="CUST-001",
            items=items,
        )
        assert invoice.subtotal == Decimal("250.00")

    def test_vat_calculation(self) -> None:
        """Test VAT calculation."""
        items = [
            LineItem(description="Item", quantity=1, unit_price=Decimal("100.00")),
        ]
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="CUST-001",
            items=items,
            vat_rate=Decimal("0.17"),
        )
        assert invoice.vat_amount == Decimal("17.00")

    def test_total_calculation(self) -> None:
        """Test total calculation."""
        items = [
            LineItem(description="Item", quantity=1, unit_price=Decimal("100.00")),
        ]
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="CUST-001",
            items=items,
            vat_rate=Decimal("0.17"),
        )
        assert invoice.total == Decimal("117.00")

    def test_empty_invoice_totals(self) -> None:
        """Test empty invoice totals."""
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="CUST-001",
        )
        assert invoice.subtotal == Decimal("0")
        assert invoice.total == Decimal("0")

    def test_balance_due_calculation(self) -> None:
        """Test balance_due calculation."""
        items = [
            LineItem(description="Item", quantity=1, unit_price=Decimal("100.00")),
        ]
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="CUST-001",
            items=items,
            vat_rate=Decimal("0.17"),
            paid_amount=Decimal("50.00"),
        )
        assert invoice.balance_due == Decimal("67.00")

    def test_add_item_method(self) -> None:
        """Test add_item method."""
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="CUST-001",
        )
        item = LineItem(description="Service", quantity=1, unit_price=Decimal("100.00"))
        invoice.add_item(item)
        assert len(invoice.items) == 1

    def test_can_transition_to(self) -> None:
        """Test status transition validation."""
        invoice = Invoice(
            id="inv-001",
            invoice_number="INV-000001",
            customer_id="CUST-001",
            status=InvoiceStatus.DRAFT,
        )
        assert invoice.can_transition_to(InvoiceStatus.ISSUED) is True
        assert invoice.can_transition_to(InvoiceStatus.PAID) is False


class TestInvoiceStatus:
    """Tests for InvoiceStatus enum."""

    def test_all_statuses(self) -> None:
        """Test all status values exist."""
        statuses = [s.value for s in InvoiceStatus]
        assert "draft" in statuses
        assert "sent" in statuses
        assert "paid" in statuses
        assert "cancelled" in statuses
        assert "overdue" in statuses
