"""
Dynamic resources - Live data that updates frequently.

Dynamic resources provide real-time data such as:
    - Customer lists and details
    - Invoice lists and details
    - Statistics and reports
"""

from __future__ import annotations

from typing import Any
from datetime import datetime
from decimal import Decimal

from invoice_mcp_server.mcp.primitives import DynamicResource
from invoice_mcp_server.domain.models import InvoiceStatus
from invoice_mcp_server.shared.logging import get_logger

logger = get_logger(__name__)


class CustomersListResource(DynamicResource):
    """
    List of all customers.

    Dynamic resource that returns current customer list.
    """

    uri = "invoice://customers/list"
    name = "Customers List"
    description = "List of all customers in the system"

    async def read(self) -> dict[str, Any]:
        """Read customers list."""
        customer_repo = self.server.get_customer_repository()
        customers = await customer_repo.list_all()

        return {
            "type": "customers_list",
            "count": len(customers),
            "data": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                }
                for c in customers
            ],
        }


class CustomerDetailResource(DynamicResource):
    """
    Customer detail resource.

    Dynamic resource for individual customer details.
    URI pattern: invoice://customers/{customer_id}
    """

    uri = "invoice://customers/{customer_id}"
    name = "Customer Detail"
    description = "Detailed information about a specific customer"

    def __init__(self, server, customer_id: str | None = None):
        """Initialize with optional customer ID."""
        super().__init__(server)
        self.customer_id = customer_id

    async def read(self) -> dict[str, Any]:
        """Read customer details."""
        if not self.customer_id:
            return {"error": "Customer ID required"}

        customer_repo = self.server.get_customer_repository()
        invoice_repo = self.server.get_invoice_repository()

        try:
            customer = await customer_repo.get(self.customer_id)
            invoices = await invoice_repo.get_by_customer(self.customer_id)

            total_invoiced = sum(inv.total for inv in invoices)
            total_paid = sum(inv.paid_amount for inv in invoices)

            return {
                "type": "customer_detail",
                "data": {
                    "id": customer.id,
                    "name": customer.name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "address": customer.address,
                    "tax_id": customer.tax_id,
                    "created_at": customer.created_at.isoformat(),
                    "statistics": {
                        "total_invoices": len(invoices),
                        "total_invoiced": str(total_invoiced),
                        "total_paid": str(total_paid),
                        "balance": str(total_invoiced - total_paid),
                    },
                },
            }
        except Exception as e:
            return {"error": str(e)}


class InvoicesListResource(DynamicResource):
    """
    List of all invoices.

    Dynamic resource that returns current invoice list.
    """

    uri = "invoice://invoices/list"
    name = "Invoices List"
    description = "List of all invoices in the system"

    async def read(self) -> dict[str, Any]:
        """Read invoices list."""
        invoice_repo = self.server.get_invoice_repository()
        invoices = await invoice_repo.list_all()

        return {
            "type": "invoices_list",
            "count": len(invoices),
            "data": [
                {
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "customer_id": inv.customer_id,
                    "status": inv.status.value,
                    "total": str(inv.total),
                    "issue_date": inv.issue_date.isoformat(),
                    "due_date": inv.due_date.isoformat() if inv.due_date else None,
                }
                for inv in invoices
            ],
        }


class InvoiceDetailResource(DynamicResource):
    """
    Invoice detail resource.

    Dynamic resource for individual invoice details.
    """

    uri = "invoice://invoices/{invoice_id}"
    name = "Invoice Detail"
    description = "Detailed information about a specific invoice"

    def __init__(self, server, invoice_id: str | None = None):
        """Initialize with optional invoice ID."""
        super().__init__(server)
        self.invoice_id = invoice_id

    async def read(self) -> dict[str, Any]:
        """Read invoice details."""
        if not self.invoice_id:
            return {"error": "Invoice ID required"}

        invoice_repo = self.server.get_invoice_repository()
        customer_repo = self.server.get_customer_repository()

        try:
            invoice = await invoice_repo.get(self.invoice_id)
            customer = await customer_repo.get(invoice.customer_id)

            return {
                "type": "invoice_detail",
                "data": {
                    "id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "invoice_type": invoice.invoice_type.value,
                    "status": invoice.status.value,
                    "customer": {
                        "id": customer.id,
                        "name": customer.name,
                        "email": customer.email,
                    },
                    "items": [
                        {
                            "id": item.id,
                            "description": item.description,
                            "quantity": str(item.quantity),
                            "unit_price": str(item.unit_price),
                            "line_total": str(item.line_total),
                        }
                        for item in invoice.items
                    ],
                    "subtotal": str(invoice.subtotal),
                    "vat_rate": str(invoice.vat_rate),
                    "vat_amount": str(invoice.vat_amount),
                    "total": str(invoice.total),
                    "paid_amount": str(invoice.paid_amount),
                    "balance_due": str(invoice.balance_due),
                    "issue_date": invoice.issue_date.isoformat(),
                    "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                    "notes": invoice.notes,
                },
            }
        except Exception as e:
            return {"error": str(e)}


class RecentInvoicesResource(DynamicResource):
    """
    Recent invoices resource.

    Dynamic resource showing most recently created invoices.
    Auto-updates with new invoice creation.
    """

    uri = "invoice://invoices/recent"
    name = "Recent Invoices"
    description = "The 5 most recently created invoices"

    async def read(self) -> dict[str, Any]:
        """Read recent invoices."""
        invoice_repo = self.server.get_invoice_repository()
        invoices = await invoice_repo.get_recent(limit=5)

        return {
            "type": "recent_invoices",
            "count": len(invoices),
            "data": [
                {
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "customer_id": inv.customer_id,
                    "status": inv.status.value,
                    "total": str(inv.total),
                    "issue_date": inv.issue_date.isoformat(),
                }
                for inv in invoices
            ],
        }


class OverdueInvoicesResource(DynamicResource):
    """
    Overdue invoices resource.

    Dynamic resource showing invoices past their due date.
    """

    uri = "invoice://invoices/overdue"
    name = "Overdue Invoices"
    description = "Invoices that are past their due date"

    async def read(self) -> dict[str, Any]:
        """Read overdue invoices."""
        invoice_repo = self.server.get_invoice_repository()
        invoices = await invoice_repo.get_overdue()

        return {
            "type": "overdue_invoices",
            "count": len(invoices),
            "data": [
                {
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "customer_id": inv.customer_id,
                    "total": str(inv.total),
                    "balance_due": str(inv.balance_due),
                    "due_date": inv.due_date.isoformat() if inv.due_date else None,
                    "days_overdue": (datetime.now().date() - inv.due_date).days if inv.due_date else 0,
                }
                for inv in invoices
            ],
        }


class StatisticsResource(DynamicResource):
    """
    System statistics resource.

    Dynamic resource providing business statistics.
    """

    uri = "invoice://statistics"
    name = "Statistics"
    description = "Business statistics and summary data"

    async def read(self) -> dict[str, Any]:
        """Read system statistics."""
        invoice_repo = self.server.get_invoice_repository()
        customer_repo = self.server.get_customer_repository()

        customers = await customer_repo.list_all()
        invoices = await invoice_repo.list_all()

        # Calculate statistics
        total_revenue = sum(inv.paid_amount for inv in invoices)
        outstanding = sum(inv.balance_due for inv in invoices if inv.status != InvoiceStatus.CANCELLED)

        status_counts = {}
        for status in InvoiceStatus:
            status_counts[status.value] = sum(1 for inv in invoices if inv.status == status)

        return {
            "type": "statistics",
            "data": {
                "customers": {
                    "total": len(customers),
                },
                "invoices": {
                    "total": len(invoices),
                    "by_status": status_counts,
                },
                "financials": {
                    "total_revenue": str(total_revenue),
                    "outstanding_balance": str(outstanding),
                    "currency": "ILS",
                },
                "generated_at": datetime.utcnow().isoformat(),
            },
        }
