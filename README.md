# Invoice MCP Server

A Model Context Protocol (MCP) server for invoice management with modular architecture.

## Documentation

- [Examples Guide](EXAMPLES.md) - Comprehensive usage examples, workflows, and error handling
- [Development Guide](DEVELOPMENT.md) - Developer setup, testing, and contributing
- [Architecture Guide](ARCHITECTURE.md) - Technical architecture and component details
- [API Reference](API_REFERENCE.md) - MCP tools, resources, and prompts reference
- [Contributing](CONTRIBUTING.md) - Contribution guidelines

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

## Quick Start

```bash
# 1. Clone and install
git clone <repository-url>
cd MCP_Server
pip install -e ".[dev]"

# 2. Test the CLI
python -m invoice_mcp_server cli customer list

# 3. Run the MCP server
python -m invoice_mcp_server stdio
```

## Installation

### Requirements
- Python 3.10+
- pip

### Install for Development
```bash
# Install with dev dependencies (pytest, mypy, ruff)
pip install -e ".[dev]"
```

### Install for Production
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

## Running the Server

### MCP Server (STDIO) - For MCP Clients
```bash
python -m invoice_mcp_server stdio
```
Use this mode when connecting from Claude Desktop or other MCP clients.

### MCP Server (HTTP)
```bash
python -m invoice_mcp_server http
```

### Web Interface
```bash
python -m invoice_mcp_server web
# Access at http://localhost:8080
```

### Help
```bash
python -m invoice_mcp_server --help
```

## CLI Reference

The CLI provides direct access to all operations for testing and management.

### Customer Commands
```bash
# List all customers
python -m invoice_mcp_server cli customer list

# Create a new customer
python -m invoice_mcp_server cli customer create --name "Acme Corp" --email "contact@acme.com"

# Create with all fields
python -m invoice_mcp_server cli customer create --name "Acme Corp" --email "contact@acme.com" --address "123 Main St" --phone "555-1234"

# Delete a customer
python -m invoice_mcp_server cli customer delete <customer-id>
```

### Invoice Commands
```bash
# List all invoices
python -m invoice_mcp_server cli invoice list

# Create a new invoice
python -m invoice_mcp_server cli invoice create --customer-id <customer-id>

# Create with due date and notes
python -m invoice_mcp_server cli invoice create --customer-id <customer-id> --due-date "2024-12-31" --notes "Project payment"

# Add item to invoice
python -m invoice_mcp_server cli invoice add-item --invoice-id <invoice-id> --description "Consulting services" --quantity 10 --price 150.00

# Send invoice
python -m invoice_mcp_server cli invoice send <invoice-id>

# Record payment
python -m invoice_mcp_server cli invoice pay --invoice-id <invoice-id> --amount 1500.00 --method "bank_transfer"
```

### Report Commands
```bash
# Show statistics
python -m invoice_mcp_server cli report stats

# Show overdue invoices
python -m invoice_mcp_server cli report overdue
```

## MCP Client Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "invoice-server": {
      "command": "python",
      "args": ["-m", "invoice_mcp_server", "stdio"],
      "cwd": "/path/to/MCP_Server"
    }
  }
}
```

### Testing MCP Connection

You can test the MCP server by sending JSON-RPC messages via stdio:

```bash
# Start the server and send an initialize request
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}' | python -m invoice_mcp_server stdio
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

### Run All Tests
```bash
pytest
```

### Run with Coverage Report
```bash
pytest --cov=src/invoice_mcp_server --cov-report=term-missing
```

### Run Specific Test Files
```bash
# Test models
pytest tests/test_models.py -v

# Test database
pytest tests/test_database.py -v

# Test SDK
pytest tests/test_sdk.py -v

# Test MCP server
pytest tests/test_mcp_server.py -v
```

### Run Tests by Pattern
```bash
# Run all customer-related tests
pytest -k "customer" -v

# Run all invoice-related tests
pytest -k "invoice" -v
```

### Code Quality
```bash
# Type checking
mypy src/invoice_mcp_server

# Linting
ruff check src/invoice_mcp_server

# Format check
ruff format --check src/invoice_mcp_server
```

## Example Workflow

```bash
# 1. Create a customer
python -m invoice_mcp_server cli customer create --name "Test Company" --email "test@company.com"
# Returns: {"id": "uuid-here", "name": "Test Company", ...}

# 2. List customers to get the ID
python -m invoice_mcp_server cli customer list

# 3. Create an invoice for the customer
python -m invoice_mcp_server cli invoice create --customer-id <customer-id-from-step-2>

# 4. Add items to the invoice
python -m invoice_mcp_server cli invoice add-item --invoice-id <invoice-id> --description "Service" --quantity 1 --price 100

# 5. Check statistics
python -m invoice_mcp_server cli report stats
```

## License

MIT
