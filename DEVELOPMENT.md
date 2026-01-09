# Development Guide

This guide covers setting up the development environment, testing, and contributing to the Invoice MCP Server.

## Prerequisites

- Python 3.10 or higher
- pip package manager
- Git

## Development Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/morenoraf/MCP_Server.git
cd MCP_Server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### 2. Verify Installation

```bash
# Run tests
pytest

# Check CLI
python -m invoice_mcp_server --help
```

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/invoice_mcp_server --cov-report=term-missing

# Specific test file
pytest tests/test_models.py -v

# By pattern
pytest -k "customer" -v
```

### Test Structure

- tests/test_models.py - Domain model tests
- tests/test_database.py - Database layer tests
- tests/test_repositories.py - Repository tests
- tests/test_sdk.py - SDK tests
- tests/test_mcp_server.py - MCP server tests

## Code Quality

```bash
# Type checking
mypy src/invoice_mcp_server

# Linting
ruff check src/invoice_mcp_server

# Format code
ruff format src/invoice_mcp_server
```

## Adding New Components

### Adding a New Tool

1. Create in src/invoice_mcp_server/mcp/tools/
2. Inherit from Tool base class
3. Define name, description, input_schema
4. Implement execute() method
5. Register in __init__.py

Example:
```python
from invoice_mcp_server.mcp.primitives import Tool
from invoice_mcp_server.mcp.protocol import ToolResult

class MyNewTool(Tool):
    name = "my_tool"
    description = "Description of my tool"

    @property
    def input_schema(self):
        return {"type": "object", "properties": {...}}

    async def execute(self, **params):
        # Implementation
        return self._json_result({"success": True})
```

### Adding a New Resource

1. Create in src/invoice_mcp_server/mcp/resources/
2. Inherit from StaticResource or DynamicResource
3. Define uri, name, description
4. Implement read() method

### Adding a New Prompt

1. Create in src/invoice_mcp_server/mcp/prompts/
2. Inherit from Prompt base class
3. Define name, description, arguments
4. Implement get_messages() method

## Project Structure

```
src/invoice_mcp_server/
    domain/         # Domain models
    gui/            # CLI and Web interfaces
    infrastructure/ # Database, repositories
    mcp/            # MCP server components
        tools/      # MCP tools
        resources/  # MCP resources
        prompts/    # MCP prompts
    sdk/            # SDK layer
    shared/         # Config, logging, exceptions
    transport/      # STDIO and HTTP transports
```

---

*Created by AI Agent 3 (Documentation)*
