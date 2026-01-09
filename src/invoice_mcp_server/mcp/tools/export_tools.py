"""
Export tools for invoices and customer data.

Tools for exporting data in various formats:
    - Export invoices to CSV
    - Export invoices to JSON
    - Export customer reports

All tools are read operations but modify output state.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime
from typing import Any, Optional

from invoice_mcp_server.mcp.primitives import Tool
from invoice_mcp_server.mcp.protocol import ToolResult
from invoice_mcp_server.domain.models import InvoiceStatus
from invoice_mcp_server.shared.logging import get_logger

logger = get_logger(__name__)


class ExportInvoicesCsvTool(Tool):
    """
    Tool to export invoices to CSV format.

    Input Data:
        - start_date (optional): Filter invoices from this date
        - end_date (optional): Filter invoices until this date
        - status (optional): Filter by invoice status
        - customer_id (optional): Filter by customer

    Output Data:
        - CSV formatted string with invoice data
    """

    name = "export_invoices_csv"
    description = "Export invoices to CSV format with optional filtering"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for export CSV parameters."""
        return {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date for filtering (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for filtering (YYYY-MM-DD)",
                },
                "status": {
                    "type": "string",
                    "enum": ["draft", "issued", "sent", "paid", "partially_paid", "overdue", "cancelled"],
                    "description": "Filter by invoice status",
                },
                "customer_id": {
                    "type": "string",
                    "description": "Filter by customer ID",
                },
            },
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute CSV export."""
        try:
            invoice_repo = self.server.get_invoice_repository()
            customer_repo = self.server.get_customer_repository()

            # Get all invoices
            invoices = await invoice_repo.list_all()

            # Apply filters
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            status_filter = params.get("status")
            customer_id = params.get("customer_id")

            if start_date:
                start = date.fromisoformat(start_date)
                invoices = [i for i in invoices if i.created_at.date() >= start]

            if end_date:
                end = date.fromisoformat(end_date)
                invoices = [i for i in invoices if i.created_at.date() <= end]

            if status_filter:
                status = InvoiceStatus(status_filter)
                invoices = [i for i in invoices if i.status == status]

            if customer_id:
                invoices = [i for i in invoices if i.customer_id == customer_id]

            # Build CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "Invoice Number",
                "Customer ID",
                "Customer Name",
                "Status",
                "Invoice Type",
                "Subtotal",
                "VAT Amount",
                "Total",
                "Paid Amount",
                "Balance Due",
                "Due Date",
                "Created At",
            ])

            # Data rows
            for invoice in invoices:
                try:
                    customer = await customer_repo.get(invoice.customer_id)
                    customer_name = customer.name
                except Exception:
                    customer_name = "Unknown"

                writer.writerow([
                    invoice.invoice_number,
                    invoice.customer_id,
                    customer_name,
                    invoice.status.value,
                    invoice.invoice_type.value,
                    str(invoice.subtotal),
                    str(invoice.vat_amount),
                    str(invoice.total),
                    str(invoice.paid_amount),
                    str(invoice.balance_due),
                    invoice.due_date.isoformat() if invoice.due_date else "",
                    invoice.created_at.isoformat(),
                ])

            csv_content = output.getvalue()
            logger.info(f"Exported {len(invoices)} invoices to CSV")

            return self._json_result({
                "success": True,
                "format": "csv",
                "record_count": len(invoices),
                "content": csv_content,
            })

        except Exception as e:
            logger.error(f"Failed to export invoices to CSV: {e}")
            return self._error_result(f"Failed to export invoices to CSV: {e}")


class ExportInvoicesJsonTool(Tool):
    """
    Tool to export invoices to JSON format.

    Input Data:
        - start_date (optional): Filter invoices from this date
        - end_date (optional): Filter invoices until this date
        - status (optional): Filter by invoice status
        - customer_id (optional): Filter by customer
        - include_items (optional): Include line items in export

    Output Data:
        - JSON formatted invoice data
    """

    name = "export_invoices_json"
    description = "Export invoices to JSON format with optional filtering"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for export JSON parameters."""
        return {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date for filtering (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for filtering (YYYY-MM-DD)",
                },
                "status": {
                    "type": "string",
                    "enum": ["draft", "issued", "sent", "paid", "partially_paid", "overdue", "cancelled"],
                    "description": "Filter by invoice status",
                },
                "customer_id": {
                    "type": "string",
                    "description": "Filter by customer ID",
                },
                "include_items": {
                    "type": "boolean",
                    "description": "Include line items in export",
                    "default": True,
                },
            },
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute JSON export."""
        try:
            invoice_repo = self.server.get_invoice_repository()
            customer_repo = self.server.get_customer_repository()

            # Get all invoices
            invoices = await invoice_repo.list_all()

            # Apply filters
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            status_filter = params.get("status")
            customer_id = params.get("customer_id")
            include_items = params.get("include_items", True)

            if start_date:
                start = date.fromisoformat(start_date)
                invoices = [i for i in invoices if i.created_at.date() >= start]

            if end_date:
                end = date.fromisoformat(end_date)
                invoices = [i for i in invoices if i.created_at.date() <= end]

            if status_filter:
                status = InvoiceStatus(status_filter)
                invoices = [i for i in invoices if i.status == status]

            if customer_id:
                invoices = [i for i in invoices if i.customer_id == customer_id]

            # Build JSON data
            export_data = []
            for invoice in invoices:
                try:
                    customer = await customer_repo.get(invoice.customer_id)
                    customer_name = customer.name
                except Exception:
                    customer_name = "Unknown"

                invoice_data = {
                    "id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_id": invoice.customer_id,
                    "customer_name": customer_name,
                    "status": invoice.status.value,
                    "invoice_type": invoice.invoice_type.value,
                    "subtotal": str(invoice.subtotal),
                    "vat_rate": str(invoice.vat_rate),
                    "vat_amount": str(invoice.vat_amount),
                    "total": str(invoice.total),
                    "paid_amount": str(invoice.paid_amount),
                    "balance_due": str(invoice.balance_due),
                    "currency": invoice.currency,
                    "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                    "notes": invoice.notes,
                    "created_at": invoice.created_at.isoformat(),
                    "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None,
                }

                if include_items:
                    invoice_data["items"] = [
                        {
                            "description": item.description,
                            "quantity": str(item.quantity),
                            "unit_price": str(item.unit_price),
                            "total": str(item.total),
                        }
                        for item in invoice.items
                    ]

                export_data.append(invoice_data)

            logger.info(f"Exported {len(invoices)} invoices to JSON")

            return self._json_result({
                "success": True,
                "format": "json",
                "record_count": len(invoices),
                "invoices": export_data,
            })

        except Exception as e:
            logger.error(f"Failed to export invoices to JSON: {e}")
            return self._error_result(f"Failed to export invoices to JSON: {e}")


class ExportCustomerReportTool(Tool):
    """
    Tool to export a comprehensive customer report.

    Input Data:
        - customer_id (optional): Specific customer to report on
        - include_invoices (optional): Include invoice details

    Output Data:
        - Comprehensive customer report with statistics
    """

    name = "export_customer_report"
    description = "Export a comprehensive customer report with invoice statistics"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for customer report parameters."""
        return {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Specific customer ID to report on (all if not specified)",
                },
                "include_invoices": {
                    "type": "boolean",
                    "description": "Include invoice summaries",
                    "default": True,
                },
            },
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute customer report export."""
        try:
            customer_repo = self.server.get_customer_repository()
            invoice_repo = self.server.get_invoice_repository()

            customer_id = params.get("customer_id")
            include_invoices = params.get("include_invoices", True)

            # Get customers
            if customer_id:
                customers = [await customer_repo.get(customer_id)]
            else:
                customers = await customer_repo.list_all()

            # Get all invoices once
            all_invoices = await invoice_repo.list_all()

            report_data = []
            for customer in customers:
                customer_invoices = [i for i in all_invoices if i.customer_id == customer.id]

                # Calculate statistics
                total_invoiced = sum(i.total for i in customer_invoices)
                total_paid = sum(i.paid_amount for i in customer_invoices)
                total_outstanding = sum(i.balance_due for i in customer_invoices)

                status_counts = {}
                for invoice in customer_invoices:
                    status = invoice.status.value
                    status_counts[status] = status_counts.get(status, 0) + 1

                customer_data = {
                    "customer": {
                        "id": customer.id,
                        "name": customer.name,
                        "email": customer.email,
                        "phone": customer.phone,
                        "address": customer.address,
                        "created_at": customer.created_at.isoformat(),
                    },
                    "statistics": {
                        "total_invoices": len(customer_invoices),
                        "total_invoiced": str(total_invoiced),
                        "total_paid": str(total_paid),
                        "total_outstanding": str(total_outstanding),
                        "status_breakdown": status_counts,
                    },
                }

                if include_invoices:
                    customer_data["invoices"] = [
                        {
                            "invoice_number": i.invoice_number,
                            "status": i.status.value,
                            "total": str(i.total),
                            "paid_amount": str(i.paid_amount),
                            "balance_due": str(i.balance_due),
                            "due_date": i.due_date.isoformat() if i.due_date else None,
                        }
                        for i in customer_invoices
                    ]

                report_data.append(customer_data)

            logger.info(f"Exported report for {len(customers)} customers")

            return self._json_result({
                "success": True,
                "report_type": "customer_report",
                "generated_at": datetime.now().isoformat(),
                "customer_count": len(customers),
                "customers": report_data,
            })

        except Exception as e:
            logger.error(f"Failed to export customer report: {e}")
            return self._error_result(f"Failed to export customer report: {e}")


def get_export_tools() -> list[type[Tool]]:
    """Get all export tools."""
    return [
        ExportInvoicesCsvTool,
        ExportInvoicesJsonTool,
        ExportCustomerReportTool,
    ]
