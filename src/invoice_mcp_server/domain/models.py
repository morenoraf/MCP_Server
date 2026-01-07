"""
Domain models for the Invoice Management System.

Defines the core business entities with validation and serialization.
All models use Pydantic for validation and JSON serialization.
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, computed_field


class InvoiceType(str, Enum):
    """Types of invoices supported by the system."""

    TAX_INVOICE = "tax_invoice"
    RECEIPT = "receipt"
    TRANSACTION = "transaction"
    CREDIT_NOTE = "credit_note"


class InvoiceStatus(str, Enum):
    """Status of an invoice in its lifecycle."""

    DRAFT = "draft"
    ISSUED = "issued"
    SENT = "sent"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class Customer(BaseModel):
    """
    Customer entity representing a client in the system.

    Input Data:
        - name: Customer name (required)
        - email: Contact email (optional)
        - phone: Contact phone (optional)
        - address: Physical address (optional)
        - tax_id: Tax identification number (optional)

    Output Data:
        - id: Unique identifier
        - All input fields
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=500)
    tax_id: str | None = Field(default=None, max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format if provided."""
        if v is not None and "@" not in v:
            raise ValueError("Invalid email format")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate phone contains only allowed characters."""
        if v is not None:
            cleaned = v.replace(" ", "").replace("-", "").replace("+", "")
            if not cleaned.isdigit():
                raise ValueError("Phone must contain only digits, spaces, dashes, and +")
        return v

    model_config = {"from_attributes": True}


class LineItem(BaseModel):
    """
    A line item in an invoice.

    Input Data:
        - description: Item description
        - quantity: Number of units
        - unit_price: Price per unit (before VAT)

    Output Data:
        - line_total: Calculated total (quantity * unit_price)
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def line_total(self) -> Decimal:
        """Calculate line total before VAT."""
        return self.quantity * self.unit_price

    model_config = {"from_attributes": True}


class Invoice(BaseModel):
    """
    Invoice entity - central business object.

    Input Data:
        - customer_id: Reference to customer
        - invoice_type: Type of invoice
        - items: List of line items
        - notes: Optional notes
        - due_date: Payment due date

    Output Data:
        - id: Unique identifier
        - invoice_number: Human-readable serial number
        - subtotal: Sum before VAT
        - vat_amount: Calculated VAT
        - total: Final total including VAT
        - status: Current status

    Setup Data (from config):
        - vat_rate: VAT percentage
        - currency: Currency code
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    invoice_number: str = Field(default="")
    customer_id: str = Field(...)
    invoice_type: InvoiceType = Field(default=InvoiceType.TAX_INVOICE)
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT)
    items: list[LineItem] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=2000)
    issue_date: date = Field(default_factory=date.today)
    due_date: date | None = Field(default=None)
    vat_rate: Decimal = Field(default=Decimal("0.17"))
    currency: str = Field(default="ILS")
    paid_amount: Decimal = Field(default=Decimal("0"))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def subtotal(self) -> Decimal:
        """Calculate subtotal before VAT."""
        return sum((item.line_total for item in self.items), Decimal("0"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def vat_amount(self) -> Decimal:
        """Calculate VAT amount."""
        return self.subtotal * self.vat_rate

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> Decimal:
        """Calculate total including VAT."""
        return self.subtotal + self.vat_amount

    @computed_field  # type: ignore[prop-decorator]
    @property
    def balance_due(self) -> Decimal:
        """Calculate remaining balance."""
        return self.total - self.paid_amount

    def add_item(self, item: LineItem) -> None:
        """Add a line item to the invoice."""
        self.items.append(item)
        self.updated_at = datetime.utcnow()

    def remove_item(self, item_id: str) -> bool:
        """Remove a line item by ID."""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                self.updated_at = datetime.utcnow()
                return True
        return False

    def can_transition_to(self, new_status: InvoiceStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions: dict[InvoiceStatus, list[InvoiceStatus]] = {
            InvoiceStatus.DRAFT: [InvoiceStatus.ISSUED, InvoiceStatus.CANCELLED],
            InvoiceStatus.ISSUED: [
                InvoiceStatus.SENT,
                InvoiceStatus.PAID,
                InvoiceStatus.PARTIALLY_PAID,
                InvoiceStatus.CANCELLED,
            ],
            InvoiceStatus.SENT: [
                InvoiceStatus.PAID,
                InvoiceStatus.PARTIALLY_PAID,
                InvoiceStatus.OVERDUE,
                InvoiceStatus.CANCELLED,
            ],
            InvoiceStatus.PARTIALLY_PAID: [
                InvoiceStatus.PAID,
                InvoiceStatus.OVERDUE,
                InvoiceStatus.CANCELLED,
            ],
            InvoiceStatus.OVERDUE: [
                InvoiceStatus.PAID,
                InvoiceStatus.PARTIALLY_PAID,
                InvoiceStatus.CANCELLED,
            ],
            InvoiceStatus.PAID: [],
            InvoiceStatus.CANCELLED: [],
        }
        return new_status in valid_transitions.get(self.status, [])

    model_config = {"from_attributes": True}


class SerialNumber(BaseModel):
    """
    Serial number generator and tracker.

    Manages sequential invoice numbers per type.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    prefix: str = Field(...)
    current_number: int = Field(default=0)
    year: int = Field(default_factory=lambda: datetime.now().year)

    def next_number(self) -> str:
        """Generate next serial number."""
        self.current_number += 1
        return f"{self.prefix}-{self.year}-{self.current_number:06d}"

    model_config = {"from_attributes": True}
