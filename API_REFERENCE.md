# API Reference

## MCP Tools

### Customer Operations

#### `create_customer`
Create a new customer in the system.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Customer full name |
| email | string | Yes | Customer email address |
| address | string | No | Physical address |
| phone | string | No | Contact phone number |

**Returns:**
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "created_at": "ISO datetime"
}
```

#### `update_customer`
Update an existing customer's information.

#### `delete_customer`
Remove a customer from the system.

---

### Invoice Operations

#### `create_invoice`
Create a new invoice for a customer.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| customer_id | uuid | Yes | Target customer ID |
| due_date | date | No | Payment due date |
| notes | string | No | Additional notes |

#### `add_invoice_item`
Add a line item to an existing invoice.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| invoice_id | uuid | Yes | Target invoice |
| description | string | Yes | Item description |
| quantity | number | Yes | Item quantity |
| price | number | Yes | Unit price |

#### `update_invoice_status`
Change the status of an invoice.

#### `record_payment`
Record a payment against an invoice.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| invoice_id | uuid | Yes | Target invoice |
| amount | number | Yes | Payment amount |
| method | string | No | Payment method |

#### `send_invoice`
Send an invoice to the customer.

---

## MCP Resources

### Configuration
- `invoice://config` - Server configuration
- `invoice://vat-rates` - VAT rate information

### Data Access
- `invoice://customers/list` - All customers
- `invoice://invoices/list` - All invoices
- `invoice://invoices/recent` - Recent invoices
- `invoice://invoices/overdue` - Overdue invoices
- `invoice://statistics/overview` - System statistics

---

## MCP Prompts

| Prompt | Description |
|--------|-------------|
| `create_invoice` | Guide for invoice creation workflow |
| `manage_customer` | Guide for customer management |
| `process_payment` | Guide for payment processing |
| `generate_report` | Guide for report generation |

---

*Documentation maintained by AI Agent 3*
