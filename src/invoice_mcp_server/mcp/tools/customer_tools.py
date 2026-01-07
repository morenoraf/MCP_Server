"""
Customer management tools.

Tools for creating, updating, and deleting customers.
All tools modify system state (Write operations).
"""

from __future__ import annotations

from typing import Any

from invoice_mcp_server.mcp.primitives import Tool
from invoice_mcp_server.mcp.protocol import ToolResult
from invoice_mcp_server.domain.models import Customer
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)


class CreateCustomerTool(Tool):
    """
    Tool to create a new customer.

    Input Data:
        - name (required): Customer name
        - email (optional): Contact email
        - phone (optional): Contact phone
        - address (optional): Physical address
        - tax_id (optional): Tax identification number

    Output Data:
        - Created customer object with generated ID
    """

    name = "create_customer"
    description = "Create a new customer in the system"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for create customer parameters."""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Customer name",
                    "minLength": 1,
                    "maxLength": 200,
                },
                "email": {
                    "type": "string",
                    "description": "Contact email address",
                    "format": "email",
                },
                "phone": {
                    "type": "string",
                    "description": "Contact phone number",
                },
                "address": {
                    "type": "string",
                    "description": "Physical address",
                },
                "tax_id": {
                    "type": "string",
                    "description": "Tax identification number",
                },
            },
            "required": ["name"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute customer creation."""
        try:
            # Validate required fields
            name = params.get("name")
            if not name:
                return self._error_result("Customer name is required")

            # Create customer object
            customer = Customer(
                name=name,
                email=params.get("email"),
                phone=params.get("phone"),
                address=params.get("address"),
                tax_id=params.get("tax_id"),
            )

            # Save to database
            customer_repo = self.server.get_customer_repository()
            created = await customer_repo.create(customer)

            logger.info(f"Customer created: {created.id} - {created.name}")

            return self._json_result({
                "success": True,
                "message": f"Customer '{created.name}' created successfully",
                "customer": created.model_dump(mode="json"),
            })

        except ValidationError as e:
            return self._error_result(str(e))
        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            return self._error_result(f"Failed to create customer: {e}")


class UpdateCustomerTool(Tool):
    """
    Tool to update an existing customer.

    Input Data:
        - customer_id (required): ID of customer to update
        - name (optional): New name
        - email (optional): New email
        - phone (optional): New phone
        - address (optional): New address
        - tax_id (optional): New tax ID

    Output Data:
        - Updated customer object
    """

    name = "update_customer"
    description = "Update an existing customer's information"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for update customer parameters."""
        return {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "ID of the customer to update",
                },
                "name": {
                    "type": "string",
                    "description": "New customer name",
                },
                "email": {
                    "type": "string",
                    "description": "New contact email",
                },
                "phone": {
                    "type": "string",
                    "description": "New contact phone",
                },
                "address": {
                    "type": "string",
                    "description": "New physical address",
                },
                "tax_id": {
                    "type": "string",
                    "description": "New tax ID",
                },
            },
            "required": ["customer_id"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute customer update."""
        try:
            customer_id = params.get("customer_id")
            if not customer_id:
                return self._error_result("Customer ID is required")

            customer_repo = self.server.get_customer_repository()

            # Get existing customer
            try:
                customer = await customer_repo.get(customer_id)
            except NotFoundError:
                return self._error_result(f"Customer not found: {customer_id}")

            # Update fields if provided
            if "name" in params and params["name"]:
                customer.name = params["name"]
            if "email" in params:
                customer.email = params["email"]
            if "phone" in params:
                customer.phone = params["phone"]
            if "address" in params:
                customer.address = params["address"]
            if "tax_id" in params:
                customer.tax_id = params["tax_id"]

            # Save updates
            updated = await customer_repo.update(customer)

            logger.info(f"Customer updated: {updated.id}")

            return self._json_result({
                "success": True,
                "message": f"Customer '{updated.name}' updated successfully",
                "customer": updated.model_dump(mode="json"),
            })

        except Exception as e:
            logger.error(f"Failed to update customer: {e}")
            return self._error_result(f"Failed to update customer: {e}")


class DeleteCustomerTool(Tool):
    """
    Tool to delete a customer.

    Input Data:
        - customer_id (required): ID of customer to delete

    Output Data:
        - Success/failure message
    """

    name = "delete_customer"
    description = "Delete a customer from the system"

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for delete customer parameters."""
        return {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "ID of the customer to delete",
                },
            },
            "required": ["customer_id"],
        }

    async def execute(self, **params: Any) -> ToolResult:
        """Execute customer deletion."""
        try:
            customer_id = params.get("customer_id")
            if not customer_id:
                return self._error_result("Customer ID is required")

            customer_repo = self.server.get_customer_repository()

            # Check if customer exists
            try:
                customer = await customer_repo.get(customer_id)
            except NotFoundError:
                return self._error_result(f"Customer not found: {customer_id}")

            # Check for existing invoices
            invoice_repo = self.server.get_invoice_repository()
            invoices = await invoice_repo.get_by_customer(customer_id)
            if invoices:
                return self._error_result(
                    f"Cannot delete customer with {len(invoices)} existing invoices"
                )

            # Delete customer
            deleted = await customer_repo.delete(customer_id)

            if deleted:
                logger.info(f"Customer deleted: {customer_id}")
                return self._success_result(
                    f"Customer '{customer.name}' deleted successfully"
                )
            else:
                return self._error_result("Failed to delete customer")

        except Exception as e:
            logger.error(f"Failed to delete customer: {e}")
            return self._error_result(f"Failed to delete customer: {e}")
