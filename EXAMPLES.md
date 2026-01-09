# Examples Guide

This document provides comprehensive examples for using the Invoice MCP Server.

## Table of Contents

- [CLI Examples](#cli-examples)
- [MCP Tool Examples](#mcp-tool-examples)
- [MCP Resource Examples](#mcp-resource-examples)
- [Common Workflows](#common-workflows)
- [Claude Desktop Integration](#claude-desktop-integration)
- [SDK Usage Examples](#sdk-usage-examples)
- [Error Handling](#error-handling)

---

## CLI Examples

### Customer Management

```bash
# Create a customer with full details
python -m invoice_mcp_server cli customer create \
  --name "TechStart Ltd" \
  --email "billing@techstart.com" \
  --address "123 Innovation Way" \
  --phone "+1-555-0123"

# List all customers
python -m invoice_mcp_server cli customer list

# Delete a customer
python -m invoice_mcp_server cli customer delete abc123-uuid
```

### Invoice Management

```bash
# Create an invoice
python -m invoice_mcp_server cli invoice create \
  --customer-id abc123-uuid \
  --due-date "2024-12-31" \
  --notes "Q4 consulting services"

# Add line items
python -m invoice_mcp_server cli invoice add-item \
  --invoice-id inv-456 \
  --description "Software Development" \
  --quantity 40 \
  --price 150.00

# Send and record payment
python -m invoice_mcp_server cli invoice send inv-456
python -m invoice_mcp_server cli invoice pay \
  --invoice-id inv-456 \
  --amount 3000.00 \
  --method "bank_transfer"
```

### Reports

```bash
python -m invoice_mcp_server cli report stats
python -m invoice_mcp_server cli report overdue
```

---

## MCP Tool Examples

### create_customer

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_customer",
    "arguments": {
      "name": "Global Tech Inc",
      "email": "accounts@globaltech.com"
    }
  }
}
```

### create_invoice

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "create_invoice",
    "arguments": {
      "customer_id": "customer-uuid",
      "invoice_type": "tax_invoice",
      "due_days": 30,
      "items": [
        {"description": "Consulting", "quantity": 20, "unit_price": 200.00}
      ]
    }
  }
}
```

### Other Tools

- update_customer, delete_customer
- add_invoice_item, send_invoice
- record_payment, update_invoice_status

---

## MCP Resource Examples

### Available Resources

| URI | Description |
|-----|-------------|
| invoice://config | Server configuration |
| invoice://vat-rates | VAT rates |
| invoice://customers/list | All customers |
| invoice://invoices/list | All invoices |
| invoice://invoices/recent | Recent invoices |
| invoice://invoices/overdue | Overdue invoices |
| invoice://statistics | Statistics |

### Reading Resources

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "resources/read",
  "params": {"uri": "invoice://customers/list"}
}
```

---

## Common Workflows

### Complete Invoice Lifecycle

```bash
# 1. Create customer
python -m invoice_mcp_server cli customer create \
  --name "New Client LLC" --email "finance@newclient.com"

# 2. Create invoice
python -m invoice_mcp_server cli invoice create \
  --customer-id cust-abc123 --due-date "2024-03-01"

# 3. Add items
python -m invoice_mcp_server cli invoice add-item \
  --invoice-id inv-xyz789 \
  --description "Development Hours" --quantity 80 --price 125.00

# 4. Send and collect payment
python -m invoice_mcp_server cli invoice send inv-xyz789
python -m invoice_mcp_server cli invoice pay \
  --invoice-id inv-xyz789 --amount 10000.00 --method "wire_transfer"
```

---

## Claude Desktop Integration

Add to claude_desktop_config.json:

```json
{
  "mcpServers": {
    "invoice-server": {
      "command": "python",
      "args": ["-m", "invoice_mcp_server", "stdio"],
      "cwd": "/path/to/MCP_Server",
      "env": {"VAT_RATE": "0.17", "CURRENCY": "ILS"}
    }
  }
}
```

---

## SDK Usage Examples

```python
import asyncio
from invoice_mcp_server.sdk.client import InvoiceSDK

async def main():
    async with InvoiceSDK() as sdk:
        # Create customer
        result = await sdk.customers.create(
            name="SDK Customer",
            email="sdk@example.com"
        )

        # List and create invoice
        customers = await sdk.customers.list_all()
        if customers:
            invoice = await sdk.invoices.create(
                customer_id=customers[0]["id"]
            )

asyncio.run(main())
```

---

## Error Handling

### Common Errors

| Error | Solution |
|-------|----------|
| Customer not found | Verify customer ID exists |
| Cannot modify invoice | Only draft invoices can be modified |
| Cannot delete customer | Delete invoices first |
| Invalid status transition | Follow: draft->issued->sent->paid |

### Error Codes

| Code | Name | Description |
|------|------|-------------|
| 1001 | VALIDATION_ERROR | Input validation failed |
| 2000 | NOT_FOUND | Resource not found |
| 3000 | INVALID_INVOICE_STATE | Invalid status transition |

---

*Created by AI Agent 3 (Documentation)*
