"""
Prompt implementations for model guidance.

Prompts provide context and instructions to guide the AI model
in performing specific tasks with the invoice system.
"""

from __future__ import annotations

from typing import Any

from invoice_mcp_server.mcp.primitives import Prompt
from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger

logger = get_logger(__name__)


class CreateInvoicePrompt(Prompt):
    """
    Prompt for guiding invoice creation.

    Provides context about invoice creation workflow,
    required fields, and validation rules.
    """

    name = "create_invoice"
    description = "Guide for creating a new invoice"

    @property
    def arguments(self) -> list[dict[str, Any]]:
        """Define prompt arguments."""
        return [
            {
                "name": "customer_name",
                "description": "Name of the customer for the invoice",
                "required": False,
            },
            {
                "name": "invoice_type",
                "description": "Type of invoice (tax_invoice, receipt, etc.)",
                "required": False,
            },
        ]

    async def get_messages(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Generate prompt messages."""
        config = Config()
        customer_name = kwargs.get("customer_name", "")
        invoice_type = kwargs.get("invoice_type", "tax_invoice")

        system_content = f"""You are an invoice management assistant. Help the user create a new invoice.

INVOICE CREATION WORKFLOW:
1. Verify or create the customer
2. Create the invoice with line items
3. Review totals and send

SYSTEM CONFIGURATION:
- VAT Rate: {config.invoice.vat_rate * 100}%
- Currency: {config.invoice.currency}
- Default Payment Terms: {config.invoice.default_payment_terms} days

AVAILABLE TOOLS:
- create_customer: Create a new customer if needed
- create_invoice: Create the invoice
- add_invoice_item: Add items to an existing invoice
- update_invoice_status: Change invoice status
- send_invoice: Send to customer

INVOICE TYPES:
- tax_invoice: Standard tax invoice with VAT
- receipt: Payment receipt
- transaction: Transaction document
- credit_note: Credit/refund note

REQUIRED INFORMATION:
- Customer (existing ID or new customer details)
- Line items (description, quantity, unit price)
- Optional: notes, custom due date"""

        user_content = f"Help me create a new {invoice_type}"
        if customer_name:
            user_content += f" for customer: {customer_name}"

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]


class ManageCustomerPrompt(Prompt):
    """
    Prompt for customer management guidance.

    Provides context about customer operations.
    """

    name = "manage_customer"
    description = "Guide for managing customers"

    @property
    def arguments(self) -> list[dict[str, Any]]:
        """Define prompt arguments."""
        return [
            {
                "name": "action",
                "description": "Action to perform (create, update, delete, view)",
                "required": False,
            },
            {
                "name": "customer_id",
                "description": "Customer ID for existing customer",
                "required": False,
            },
        ]

    async def get_messages(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Generate prompt messages."""
        action = kwargs.get("action", "view")
        customer_id = kwargs.get("customer_id", "")

        system_content = """You are a customer management assistant. Help manage customer records.

AVAILABLE OPERATIONS:
1. View - List all customers or view specific customer details
2. Create - Add a new customer to the system
3. Update - Modify existing customer information
4. Delete - Remove a customer (only if no invoices exist)

CUSTOMER FIELDS:
- name (required): Full business or individual name
- email: Contact email address
- phone: Contact phone number
- address: Physical/billing address
- tax_id: Tax identification number (for business invoicing)

TOOLS TO USE:
- create_customer: Create new customer
- update_customer: Update existing customer
- delete_customer: Remove customer

RESOURCES TO READ:
- invoice://customers/list: Get all customers
- invoice://customers/{id}: Get specific customer details

IMPORTANT NOTES:
- Cannot delete customers with existing invoices
- Customer ID is auto-generated
- All changes are logged"""

        user_content = f"Help me {action} a customer"
        if customer_id:
            user_content += f" (ID: {customer_id})"

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]


class ProcessPaymentPrompt(Prompt):
    """
    Prompt for payment processing guidance.

    Provides context about recording payments and status updates.
    """

    name = "process_payment"
    description = "Guide for processing payments on invoices"

    @property
    def arguments(self) -> list[dict[str, Any]]:
        """Define prompt arguments."""
        return [
            {
                "name": "invoice_number",
                "description": "Invoice number to process payment for",
                "required": False,
            },
            {
                "name": "amount",
                "description": "Payment amount",
                "required": False,
            },
        ]

    async def get_messages(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Generate prompt messages."""
        config = Config()
        invoice_number = kwargs.get("invoice_number", "")
        amount = kwargs.get("amount", "")

        system_content = f"""You are a payment processing assistant. Help record and manage payments.

PAYMENT WORKFLOW:
1. Identify the invoice (by number or ID)
2. Verify the outstanding balance
3. Record the payment amount
4. System automatically updates status

PAYMENT STATUS RULES:
- Full payment → Status becomes 'paid'
- Partial payment → Status becomes 'partially_paid'
- Cannot record payment on cancelled or draft invoices

TOOLS TO USE:
- record_payment: Record a payment on an invoice

RESOURCES TO CHECK:
- invoice://invoices/{{id}}: Get invoice details including balance
- invoice://invoices/overdue: View overdue invoices

CURRENCY: {config.invoice.currency}

IMPORTANT:
- Payment amount must be positive
- Overpayment is allowed (credit will show as negative balance)
- All payments are logged with timestamp"""

        user_content = "Help me record a payment"
        if invoice_number:
            user_content += f" for invoice {invoice_number}"
        if amount:
            user_content += f" (amount: {amount})"

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]


class GenerateReportPrompt(Prompt):
    """
    Prompt for report generation guidance.

    Provides context about available reports and data analysis.
    """

    name = "generate_report"
    description = "Guide for generating business reports"

    @property
    def arguments(self) -> list[dict[str, Any]]:
        """Define prompt arguments."""
        return [
            {
                "name": "report_type",
                "description": "Type of report (summary, overdue, customer, etc.)",
                "required": False,
            },
        ]

    async def get_messages(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Generate prompt messages."""
        report_type = kwargs.get("report_type", "summary")

        system_content = """You are a business reporting assistant. Help generate and analyze reports.

AVAILABLE REPORTS:

1. SUMMARY REPORT
   Resource: invoice://statistics
   Shows: Total customers, invoices, revenue, outstanding balance

2. OVERDUE REPORT
   Resource: invoice://invoices/overdue
   Shows: Invoices past due date with days overdue

3. RECENT ACTIVITY
   Resource: invoice://invoices/recent
   Shows: 5 most recently created invoices

4. CUSTOMER REPORT
   Resource: invoice://customers/list
   Then: invoice://customers/{id} for details
   Shows: Customer list with invoice history

5. STATUS BREAKDOWN
   Resource: invoice://statistics
   Shows: Invoices grouped by status

HOW TO GENERATE:
1. Read the appropriate resource(s)
2. Analyze the returned data
3. Present findings in clear format

DATA ANALYSIS TIPS:
- Compare totals vs outstanding for cash flow
- Identify customers with high balances
- Track overdue invoices for follow-up
- Monitor invoice status distribution"""

        user_content = f"Generate a {report_type} report"

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]
