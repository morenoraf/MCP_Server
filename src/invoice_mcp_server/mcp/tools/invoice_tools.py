"""
Invoice management tools.

Tools for creating and managing invoices, payments, and sending.
All tools modify system state (Write operations).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from invoice_mcp_server.mcp.primitives import Tool
from invoice_mcp_server.mcp.protocol import ToolResult
from invoice_mcp_server.domain.models import (
    Invoice,
    InvoiceType,
    InvoiceStatus,
    LineItem,
)
from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import NotFoundError

logger = get_logger(__name__)


class CreateInvoiceTool(Tool):
    """
    Tool to create a new invoice.

    Input Data:
        - customer_id (required): Customer ID
        - invoice_type (optional): Type of invoice
        - items (optional): List of line items
        - notes (optional): Invoice notes
        - due_days (optional): Days until due

    Output Data:
        - Created invoice with generated number
    """

    name = "create_invoice"
    description = "Create a new invoice for a customer"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for create invoice parameters."""
        return {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "ID of the customer",
                },
                "invoice_type": {
                    "type": "string",
                    "enum": ["tax_invoice", "receipt", "transaction", "credit_note"],
                    "description": "Type of invoice",
                    "default": "tax_invoice",
                },
                "items": {
                    "type": "array",
                    "description": "Line items",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number", "minimum": 0},
                            "unit_price": {"type": "number", "minimum": 0},
                        },
                        "required": ["description", "quantity", "unit_price"],
                    },
                },
                "notes": {
                    "type": "string",
                    "description": "Invoice notes",
                },
                "due_days": {
                    "type": "integer",
                    "description": "Days until payment due",
                    "default": 30,
                },
            },
            "required": ["customer_id"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute invoice creation."""
        try:
            customer_id = params.get("customer_id")
            if not customer_id:
                return self._error_result("Customer ID is required")

            # Verify customer exists
            customer_repo = self.server.get_customer_repository()
            try:
                await customer_repo.get(customer_id)
            except NotFoundError:
                return self._error_result(f"Customer not found: {customer_id}")

            config = Config()

            # Create line items
            items = []
            for item_data in params.get("items", []):
                items.append(LineItem(
                    description=item_data["description"],
                    quantity=Decimal(str(item_data["quantity"])),
                    unit_price=Decimal(str(item_data["unit_price"])),
                ))

            # Calculate due date
            due_days = params.get("due_days", config.invoice.default_payment_terms)
            due_date = date.today() + timedelta(days=due_days)

            # Create invoice
            invoice_type_str = params.get("invoice_type", "tax_invoice")
            invoice = Invoice(
                customer_id=customer_id,
                invoice_type=InvoiceType(invoice_type_str),
                items=items,
                notes=params.get("notes"),
                due_date=due_date,
                vat_rate=Decimal(str(config.invoice.vat_rate)),
                currency=config.invoice.currency,
            )

            # Save to database
            invoice_repo = self.server.get_invoice_repository()
            created = await invoice_repo.create(invoice)

            logger.info(f"Invoice created: {created.invoice_number}")

            return self._json_result({
                "success": True,
                "message": f"Invoice {created.invoice_number} created successfully",
                "invoice": {
                    "id": created.id,
                    "invoice_number": created.invoice_number,
                    "customer_id": created.customer_id,
                    "status": created.status.value,
                    "subtotal": str(created.subtotal),
                    "vat_amount": str(created.vat_amount),
                    "total": str(created.total),
                    "due_date": created.due_date.isoformat() if created.due_date else None,
                },
            })

        except Exception as e:
            logger.error(f"Failed to create invoice: {e}")
            return self._error_result(f"Failed to create invoice: {e}")


class AddInvoiceItemTool(Tool):
    """
    Tool to add a line item to an existing invoice.

    Input Data:
        - invoice_id (required): Invoice ID
        - description (required): Item description
        - quantity (required): Quantity
        - unit_price (required): Price per unit

    Output Data:
        - Updated invoice with new totals
    """

    name = "add_invoice_item"
    description = "Add a line item to an existing invoice"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for add item parameters."""
        return {
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": "ID of the invoice",
                },
                "description": {
                    "type": "string",
                    "description": "Item description",
                },
                "quantity": {
                    "type": "number",
                    "description": "Quantity",
                    "minimum": 0,
                },
                "unit_price": {
                    "type": "number",
                    "description": "Price per unit",
                    "minimum": 0,
                },
            },
            "required": ["invoice_id", "description", "quantity", "unit_price"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute adding line item."""
        try:
            invoice_id = params.get("invoice_id")
            if not invoice_id:
                return self._error_result("Invoice ID is required")

            invoice_repo = self.server.get_invoice_repository()

            # Get invoice
            try:
                invoice = await invoice_repo.get(invoice_id)
            except NotFoundError:
                return self._error_result(f"Invoice not found: {invoice_id}")

            # Check if invoice can be modified
            if invoice.status not in [InvoiceStatus.DRAFT]:
                return self._error_result(
                    f"Cannot modify invoice in {invoice.status.value} status"
                )

            # Create and add item
            item = LineItem(
                description=params["description"],
                quantity=Decimal(str(params["quantity"])),
                unit_price=Decimal(str(params["unit_price"])),
            )
            invoice.add_item(item)

            # Save changes
            updated = await invoice_repo.update(invoice)

            logger.info(f"Item added to invoice: {updated.invoice_number}")

            return self._json_result({
                "success": True,
                "message": f"Item added to invoice {updated.invoice_number}",
                "invoice": {
                    "id": updated.id,
                    "invoice_number": updated.invoice_number,
                    "item_count": len(updated.items),
                    "subtotal": str(updated.subtotal),
                    "total": str(updated.total),
                },
            })

        except Exception as e:
            logger.error(f"Failed to add invoice item: {e}")
            return self._error_result(f"Failed to add invoice item: {e}")


class UpdateInvoiceStatusTool(Tool):
    """
    Tool to update invoice status.

    Input Data:
        - invoice_id (required): Invoice ID
        - status (required): New status

    Output Data:
        - Updated invoice
    """

    name = "update_invoice_status"
    description = "Update the status of an invoice"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for status update parameters."""
        return {
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": "ID of the invoice",
                },
                "status": {
                    "type": "string",
                    "enum": [s.value for s in InvoiceStatus],
                    "description": "New status",
                },
            },
            "required": ["invoice_id", "status"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute status update."""
        try:
            invoice_id = params.get("invoice_id")
            new_status_str = params.get("status")

            if not invoice_id or not new_status_str:
                return self._error_result("Invoice ID and status are required")

            new_status = InvoiceStatus(new_status_str)
            invoice_repo = self.server.get_invoice_repository()

            # Get invoice
            try:
                invoice = await invoice_repo.get(invoice_id)
            except NotFoundError:
                return self._error_result(f"Invoice not found: {invoice_id}")

            # Check valid transition
            if not invoice.can_transition_to(new_status):
                return self._error_result(
                    f"Cannot transition from {invoice.status.value} to {new_status.value}"
                )

            # Update status
            old_status = invoice.status
            invoice.status = new_status

            # Save changes
            updated = await invoice_repo.update(invoice)

            logger.info(
                f"Invoice status updated: {updated.invoice_number} "
                f"({old_status.value} -> {new_status.value})"
            )

            return self._json_result({
                "success": True,
                "message": f"Invoice {updated.invoice_number} status updated to {new_status.value}",
                "invoice": {
                    "id": updated.id,
                    "invoice_number": updated.invoice_number,
                    "old_status": old_status.value,
                    "new_status": updated.status.value,
                },
            })

        except Exception as e:
            logger.error(f"Failed to update invoice status: {e}")
            return self._error_result(f"Failed to update invoice status: {e}")


class RecordPaymentTool(Tool):
    """
    Tool to record a payment on an invoice.

    Input Data:
        - invoice_id (required): Invoice ID
        - amount (required): Payment amount

    Output Data:
        - Updated invoice with payment recorded
    """

    name = "record_payment"
    description = "Record a payment on an invoice"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for payment recording parameters."""
        return {
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": "ID of the invoice",
                },
                "amount": {
                    "type": "number",
                    "description": "Payment amount",
                    "minimum": 0,
                },
            },
            "required": ["invoice_id", "amount"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute payment recording."""
        try:
            invoice_id = params.get("invoice_id")
            amount = params.get("amount")

            if not invoice_id or amount is None:
                return self._error_result("Invoice ID and amount are required")

            payment_amount = Decimal(str(amount))
            if payment_amount <= 0:
                return self._error_result("Payment amount must be positive")

            invoice_repo = self.server.get_invoice_repository()

            # Get invoice
            try:
                invoice = await invoice_repo.get(invoice_id)
            except NotFoundError:
                return self._error_result(f"Invoice not found: {invoice_id}")

            # Check if payment can be recorded
            if invoice.status in [InvoiceStatus.CANCELLED, InvoiceStatus.DRAFT]:
                return self._error_result(
                    f"Cannot record payment on {invoice.status.value} invoice"
                )

            # Record payment
            invoice.paid_amount += payment_amount

            # Update status based on payment
            if invoice.paid_amount >= invoice.total:
                invoice.status = InvoiceStatus.PAID
            elif invoice.paid_amount > 0:
                invoice.status = InvoiceStatus.PARTIALLY_PAID

            # Save changes
            updated = await invoice_repo.update(invoice)

            logger.info(
                f"Payment recorded: {updated.invoice_number} - {payment_amount}"
            )

            return self._json_result({
                "success": True,
                "message": f"Payment of {payment_amount} recorded on invoice {updated.invoice_number}",
                "invoice": {
                    "id": updated.id,
                    "invoice_number": updated.invoice_number,
                    "total": str(updated.total),
                    "paid_amount": str(updated.paid_amount),
                    "balance_due": str(updated.balance_due),
                    "status": updated.status.value,
                },
            })

        except Exception as e:
            logger.error(f"Failed to record payment: {e}")
            return self._error_result(f"Failed to record payment: {e}")


class SendInvoiceTool(Tool):
    """
    Tool to send an invoice to the customer.

    Input Data:
        - invoice_id (required): Invoice ID

    Output Data:
        - Confirmation of sending
    """

    name = "send_invoice"
    description = "Send an invoice to the customer"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for send invoice parameters."""
        return {
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": "ID of the invoice to send",
                },
            },
            "required": ["invoice_id"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute invoice sending."""
        try:
            invoice_id = params.get("invoice_id")
            if not invoice_id:
                return self._error_result("Invoice ID is required")

            invoice_repo = self.server.get_invoice_repository()
            customer_repo = self.server.get_customer_repository()

            # Get invoice
            try:
                invoice = await invoice_repo.get(invoice_id)
            except NotFoundError:
                return self._error_result(f"Invoice not found: {invoice_id}")

            # Check if invoice can be sent
            if invoice.status == InvoiceStatus.DRAFT:
                # Auto-issue before sending
                invoice.status = InvoiceStatus.ISSUED

            if invoice.status not in [InvoiceStatus.ISSUED, InvoiceStatus.SENT]:
                return self._error_result(
                    f"Cannot send invoice in {invoice.status.value} status"
                )

            # Get customer for email
            customer = await customer_repo.get(invoice.customer_id)

            # Simulate sending (in real implementation, would send email)
            invoice.status = InvoiceStatus.SENT

            # Save changes
            updated = await invoice_repo.update(invoice)

            logger.info(f"Invoice sent: {updated.invoice_number} to {customer.email}")

            return self._json_result({
                "success": True,
                "message": f"Invoice {updated.invoice_number} sent to {customer.name}",
                "invoice": {
                    "id": updated.id,
                    "invoice_number": updated.invoice_number,
                    "status": updated.status.value,
                    "sent_to": customer.email or customer.name,
                },
            })

        except Exception as e:
            logger.error(f"Failed to send invoice: {e}")
            return self._error_result(f"Failed to send invoice: {e}")
