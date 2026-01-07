# Invoice MCP Server

A Model Context Protocol (MCP) server for invoice management with modular architecture.

## Features

- **MCP Protocol Support**: Full implementation of Tools, Resources, and Prompts
- **Multiple Transports**: STDIO and HTTP/SSE support
- **Dual GUI**: CLI and Web interfaces
- **SDK Layer**: All operations through unified SDK
- **Modular Design**: Swappable components without code changes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      GUI Layer                              │
│              ┌─────────┐    ┌─────────┐                     │
│              │   CLI   │    │   Web   │                     │
│              └────┬────┘    └────┬────┘                     │
├───────────────────┴──────────────┴──────────────────────────┤
│                      SDK Layer                              │
│   CustomerOperations │ InvoiceOperations │ ReportOperations │
├─────────────────────────────────────────────────────────────┤
│                    MCP Server                               │
│   ┌─────────┐    ┌───────────┐    ┌─────────┐              │
│   │  Tools  │    │ Resources │    │ Prompts │              │
│   └─────────┘    └───────────┘    └─────────┘              │
├─────────────────────────────────────────────────────────────┤
│                  Transport Layer                            │
│              ┌─────────┐    ┌─────────┐                     │
│              │  STDIO  │    │  HTTP   │                     │
│              └─────────┘    └─────────┘                     │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure                              │
│     Database │ Repositories │ Lock Manager │ Config         │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install -e .
```

## Configuration

All configuration via environment variables or `.env` file:

```env
# Server
SERVER_HOST=127.0.0.1
SERVER_PORT=8080

# Database
DB_PATH=data/invoices.db

# Invoice
VAT_RATE=0.17
CURRENCY=ILS

# Transport
TRANSPORT_TYPE=stdio

# Logging
LOG_LEVEL=INFO
```

## Usage

### MCP Server (STDIO)
```bash
python -m invoice_mcp_server stdio
```

### MCP Server (HTTP)
```bash
python -m invoice_mcp_server http
```

### CLI Interface
```bash
python -m invoice_mcp_server cli customer list
python -m invoice_mcp_server cli invoice create --customer-id CUST-001
```

### Web Interface
```bash
python -m invoice_mcp_server web
# Access at http://localhost:8080
```

## MCP Primitives

### Tools (Write Operations)
- `create_customer` - Create new customer
- `update_customer` - Update customer details
- `delete_customer` - Delete customer
- `create_invoice` - Create new invoice
- `add_invoice_item` - Add item to invoice
- `update_invoice_status` - Change invoice status
- `record_payment` - Record payment
- `send_invoice` - Send invoice to customer

### Resources (Read Operations)
- `invoice://config` - Server configuration
- `invoice://vat-rates` - VAT rates
- `invoice://customers/list` - Customer list
- `invoice://invoices/list` - Invoice list
- `invoice://invoices/recent` - Recent invoices
- `invoice://invoices/overdue` - Overdue invoices
- `invoice://statistics/overview` - Statistics

### Prompts (Model Guidance)
- `create_invoice` - Guide for invoice creation
- `manage_customer` - Guide for customer management
- `process_payment` - Guide for payment processing
- `generate_report` - Guide for report generation

## Testing

```bash
pytest tests/ -v --cov=invoice_mcp_server
```

## License

MIT
