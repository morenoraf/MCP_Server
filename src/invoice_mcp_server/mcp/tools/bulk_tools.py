"""
Bulk invoice operations tools.

Tools for performing batch operations on invoices:
    - Bulk create invoices
    - Bulk update invoice statuses
    - Bulk delete invoices

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


class BulkCreateInvoicesTool(Tool):
    """
    Tool to create multiple invoices in a single operation.

    Input Data:
        - invoices (required): List of invoice specifications
            - customer_id (required): Customer ID
            - invoice_type (optional): Type of invoice
            - items (optional): List of line items
            - notes (optional): Invoice notes
            - due_days (optional): Days until due

    Output Data:
        - List of created invoices with their IDs and numbers
        - Summary of successful and failed creations
    """

    name = "bulk_create_invoices"
    description = "Create multiple invoices in a single batch operation"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for bulk create invoices parameters."""
        return {
            "type": "object",
            "properties": {
                "invoices": {
                    "type": "array",
                    "description": "List of invoices to create",
                    "items": {
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
                    },
                    "minItems": 1,
                },
            },
            "required": ["invoices"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute bulk invoice creation."""
        try:
            invoices_data = params.get("invoices", [])
            if not invoices_data:
                return self._error_result("At least one invoice specification is required")

            config = Config()
            customer_repo = self.server.get_customer_repository()
            invoice_repo = self.server.get_invoice_repository()

            created_invoices = []
            failed_invoices = []

            for idx, invoice_data in enumerate(invoices_data):
                try:
                    customer_id = invoice_data.get("customer_id")
                    if not customer_id:
                        failed_invoices.append({
                            "index": idx,
                            "error": "Customer ID is required",
                        })
                        continue

                    # Verify customer exists
                    try:
                        await customer_repo.get(customer_id)
                    except NotFoundError:
                        failed_invoices.append({
                            "index": idx,
                            "error": f"Customer not found: {customer_id}",
                        })
                        continue

                    # Create line items
                    items = []
                    for item_data in invoice_data.get("items", []):
                        items.append(LineItem(
                            description=item_data["description"],
                            quantity=Decimal(str(item_data["quantity"])),
                            unit_price=Decimal(str(item_data["unit_price"])),
                        ))

                    # Calculate due date
                    due_days = invoice_data.get("due_days", config.invoice.default_payment_terms)
                    due_date = date.today() + timedelta(days=due_days)

                    # Create invoice
                    invoice_type_str = invoice_data.get("invoice_type", "tax_invoice")
                    invoice = Invoice(
                        customer_id=customer_id,
                        invoice_type=InvoiceType(invoice_type_str),
                        items=items,
                        notes=invoice_data.get("notes"),
                        due_date=due_date,
                        vat_rate=Decimal(str(config.invoice.vat_rate)),
                        currency=config.invoice.currency,
                    )

                    # Save to database
                    created = await invoice_repo.create(invoice)

                    created_invoices.append({
                        "index": idx,
                        "id": created.id,
                        "invoice_number": created.invoice_number,
                        "customer_id": created.customer_id,
                        "total": str(created.total),
                    })

                    logger.info(f"Bulk create - Invoice created: {created.invoice_number}")

                except Exception as e:
                    failed_invoices.append({
                        "index": idx,
                        "error": str(e),
                    })
                    logger.error(f"Bulk create - Failed to create invoice at index {idx}: {e}")

            return self._json_result({
                "success": True,
                "message": f"Bulk creation completed: {len(created_invoices)} succeeded, {len(failed_invoices)} failed",
                "created_count": len(created_invoices),
                "failed_count": len(failed_invoices),
                "created_invoices": created_invoices,
                "failed_invoices": failed_invoices,
            })

        except Exception as e:
            logger.error(f"Failed to execute bulk create invoices: {e}")
            return self._error_result(f"Failed to execute bulk create invoices: {e}")


class BulkUpdateStatusTool(Tool):
    """
    Tool to update the status of multiple invoices at once.

    Input Data:
        - invoice_ids (required): List of invoice IDs to update
        - status (required): New status to apply to all invoices

    Output Data:
        - Summary of successful and failed updates
    """

    name = "bulk_update_status"
    description = "Update the status of multiple invoices in a single operation"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for bulk update status parameters."""
        return {
            "type": "object",
            "properties": {
                "invoice_ids": {
                    "type": "array",
                    "description": "List of invoice IDs to update",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
                "status": {
                    "type": "string",
                    "enum": ["draft", "issued", "sent", "paid", "partially_paid", "overdue", "cancelled"],
                    "description": "New status to apply to all invoices",
                },
            },
            "required": ["invoice_ids", "status"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute bulk status update."""
        try:
            invoice_ids = params.get("invoice_ids", [])
            new_status_str = params.get("status")

            if not invoice_ids:
                return self._error_result("At least one invoice ID is required")

            if not new_status_str:
                return self._error_result("Status is required")

            new_status = InvoiceStatus(new_status_str)
            invoice_repo = self.server.get_invoice_repository()

            updated_invoices = []
            failed_updates = []

            for invoice_id in invoice_ids:
                try:
                    invoice = await invoice_repo.get(invoice_id)
                    old_status = invoice.status
                    invoice.status = new_status
                    updated = await invoice_repo.update(invoice)

                    updated_invoices.append({
                        "invoice_id": updated.id,
                        "invoice_number": updated.invoice_number,
                        "old_status": old_status.value,
                        "new_status": updated.status.value,
                    })

                    logger.info(f"Bulk status update - {updated.invoice_number}: {old_status.value} -> {new_status.value}")

                except NotFoundError:
                    failed_updates.append({
                        "invoice_id": invoice_id,
                        "error": "Invoice not found",
                    })
                except Exception as e:
                    failed_updates.append({
                        "invoice_id": invoice_id,
                        "error": str(e),
                    })
                    logger.error(f"Bulk status update - Failed for {invoice_id}: {e}")

            return self._json_result({
                "success": True,
                "message": f"Bulk status update completed: {len(updated_invoices)} succeeded, {len(failed_updates)} failed",
                "target_status": new_status.value,
                "updated_count": len(updated_invoices),
                "failed_count": len(failed_updates),
                "updated_invoices": updated_invoices,
                "failed_updates": failed_updates,
            })

        except Exception as e:
            logger.error(f"Failed to execute bulk status update: {e}")
            return self._error_result(f"Failed to execute bulk status update: {e}")


class BulkDeleteInvoicesTool(Tool):
    """
    Tool to delete multiple invoices at once.

    Input Data:
        - invoice_ids (required): List of invoice IDs to delete
        - force (optional): If true, allows deletion of non-draft invoices

    Output Data:
        - Summary of successful and failed deletions
    """

    name = "bulk_delete_invoices"
    description = "Delete multiple invoices in a single operation"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for bulk delete invoices parameters."""
        return {
            "type": "object",
            "properties": {
                "invoice_ids": {
                    "type": "array",
                    "description": "List of invoice IDs to delete",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
                "force": {
                    "type": "boolean",
                    "description": "Force deletion of non-draft invoices",
                    "default": False,
                },
            },
            "required": ["invoice_ids"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute bulk invoice deletion."""
        try:
            invoice_ids = params.get("invoice_ids", [])
            force = params.get("force", False)

            if not invoice_ids:
                return self._error_result("At least one invoice ID is required")

            invoice_repo = self.server.get_invoice_repository()

            deleted_invoices = []
            failed_deletions = []

            for invoice_id in invoice_ids:
                try:
                    invoice = await invoice_repo.get(invoice_id)

                    if not force and invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED]:
                        failed_deletions.append({
                            "invoice_id": invoice_id,
                            "invoice_number": invoice.invoice_number,
                            "error": f"Cannot delete invoice in {invoice.status.value} status without force=true",
                        })
                        continue

                    deleted = await invoice_repo.delete(invoice_id)

                    if deleted:
                        deleted_invoices.append({
                            "invoice_id": invoice_id,
                            "invoice_number": invoice.invoice_number,
                        })
                        logger.info(f"Bulk delete - Invoice deleted: {invoice.invoice_number}")

                except NotFoundError:
                    failed_deletions.append({
                        "invoice_id": invoice_id,
                        "error": "Invoice not found",
                    })
                except Exception as e:
                    failed_deletions.append({
                        "invoice_id": invoice_id,
                        "error": str(e),
                    })
                    logger.error(f"Bulk delete - Failed for {invoice_id}: {e}")

            return self._json_result({
                "success": True,
                "message": f"Bulk deletion completed: {len(deleted_invoices)} succeeded, {len(failed_deletions)} failed",
                "deleted_count": len(deleted_invoices),
                "failed_count": len(failed_deletions),
                "deleted_invoices": deleted_invoices,
                "failed_deletions": failed_deletions,
            })

        except Exception as e:
            logger.error(f"Failed to execute bulk delete invoices: {e}")
            return self._error_result(f"Failed to execute bulk delete invoices: {e}")


def get_bulk_tools() -> list[type[Tool]]:
    """Get all bulk operation tools."""
    return [
        BulkCreateInvoicesTool,
        BulkUpdateStatusTool,
        BulkDeleteInvoicesTool,
    ]
