"""
SDK Operations - High-level operation modules.

Provides typed, convenient methods for common operations.
All methods delegate to the SDK client's tool/resource calls.
"""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

from invoice_mcp_server.shared.logging import get_logger

if TYPE_CHECKING:
    from invoice_mcp_server.sdk.client import InvoiceSDK

logger = get_logger(__name__)


def _extract_data(result: dict[str, Any]) -> Any:
    """Extract data from MCP resource response."""
    contents = result.get("contents", [])
    if not contents:
        return None

    text = contents[0].get("text", "{}")
    data = json.loads(text)

    # Resources return {"type": "...", "data": [...]}
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


class CustomerOperations:
    """High-level customer operations."""

    def __init__(self, sdk: InvoiceSDK) -> None:
        """Initialize with SDK reference."""
        self._sdk = sdk

    async def create(
        self,
        name: str,
        email: str,
        address: str | None = None,
        phone: str | None = None,
    ) -> dict[str, Any]:
        """Create a new customer."""
        args = {"name": name, "email": email}
        if address:
            args["address"] = address
        if phone:
            args["phone"] = phone

        result = await self._sdk.call_tool("create_customer", args)
        logger.info(f"Created customer: {name}")
        return result

    async def update(self, customer_id: str, **fields: Any) -> dict[str, Any]:
        """Update customer fields."""
        args = {"customer_id": customer_id, **fields}
        result = await self._sdk.call_tool("update_customer", args)
        logger.info(f"Updated customer: {customer_id}")
        return result

    async def delete(self, customer_id: str) -> dict[str, Any]:
        """Delete a customer."""
        result = await self._sdk.call_tool("delete_customer", {"customer_id": customer_id})
        logger.info(f"Deleted customer: {customer_id}")
        return result

    async def list_all(self) -> list[dict[str, Any]]:
        """List all customers."""
        result = await self._sdk.read_resource("invoice://customers/list")
        data = _extract_data(result)
        if isinstance(data, list):
            return data
        return []

    async def get(self, customer_id: str) -> dict[str, Any] | None:
        """Get a specific customer by ID."""
        customers = await self.list_all()
        for customer in customers:
            if isinstance(customer, dict) and customer.get("id") == customer_id:
                return customer
        return None


class InvoiceOperations:
    """High-level invoice operations."""

    def __init__(self, sdk: InvoiceSDK) -> None:
        """Initialize with SDK reference."""
        self._sdk = sdk

    async def create(
        self,
        customer_id: str,
        due_date: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a new invoice."""
        args = {"customer_id": customer_id}
        if due_date:
            args["due_date"] = due_date
        if notes:
            args["notes"] = notes

        result = await self._sdk.call_tool("create_invoice", args)
        logger.info(f"Created invoice for customer: {customer_id}")
        return result

    async def add_item(
        self,
        invoice_id: str,
        description: str,
        quantity: int,
        unit_price: float,
    ) -> dict[str, Any]:
        """Add an item to an invoice."""
        result = await self._sdk.call_tool(
            "add_invoice_item",
            {
                "invoice_id": invoice_id,
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
            },
        )
        logger.info(f"Added item to invoice: {invoice_id}")
        return result

    async def send(self, invoice_id: str) -> dict[str, Any]:
        """Send an invoice to the customer."""
        result = await self._sdk.call_tool("send_invoice", {"invoice_id": invoice_id})
        logger.info(f"Sent invoice: {invoice_id}")
        return result

    async def record_payment(
        self,
        invoice_id: str,
        amount: float,
        payment_method: str,
    ) -> dict[str, Any]:
        """Record a payment for an invoice."""
        result = await self._sdk.call_tool(
            "record_payment",
            {
                "invoice_id": invoice_id,
                "amount": amount,
                "payment_method": payment_method,
            },
        )
        logger.info(f"Recorded payment for invoice: {invoice_id}")
        return result

    async def list_all(self) -> list[dict[str, Any]]:
        """List all invoices."""
        result = await self._sdk.read_resource("invoice://invoices/list")
        data = _extract_data(result)
        if isinstance(data, list):
            return data
        return []

    async def get_overdue(self) -> list[dict[str, Any]]:
        """Get overdue invoices."""
        result = await self._sdk.read_resource("invoice://invoices/overdue")
        data = _extract_data(result)
        if isinstance(data, list):
            return data
        return []


class ReportOperations:
    """High-level report and statistics operations."""

    def __init__(self, sdk: InvoiceSDK) -> None:
        """Initialize with SDK reference."""
        self._sdk = sdk

    async def get_statistics(self) -> dict[str, Any]:
        """Get overall statistics."""
        result = await self._sdk.read_resource("invoice://statistics")
        data = _extract_data(result)
        if isinstance(data, dict):
            return data
        return {}

    async def get_recent_invoices(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent invoices."""
        result = await self._sdk.read_resource("invoice://invoices/recent")
        data = _extract_data(result)
        if isinstance(data, list):
            return data[:limit]
        return []

    async def get_config(self) -> dict[str, Any]:
        """Get server configuration."""
        result = await self._sdk.read_resource("invoice://config")
        data = _extract_data(result)
        if isinstance(data, dict):
            return data
        return {}

    async def get_vat_rates(self) -> dict[str, Any]:
        """Get VAT rates configuration."""
        result = await self._sdk.read_resource("invoice://vat-rates")
        data = _extract_data(result)
        if isinstance(data, dict):
            return data
        return {}
