# Architecture Guide

This document describes the technical architecture of the Invoice MCP Server.

## Overview

The Invoice MCP Server implements a layered architecture with clear separation of concerns.

## Architecture Diagram

```
+-------------------------------------------------------------+
|                       GUI Layer                              |
|               +----------+    +----------+                   |
|               |   CLI    |    |   Web    |                   |
|               +----+-----+    +----+-----+                   |
+--------------------|--------------+|-------------------------+
|                    SDK Layer                                 |
|   CustomerOperations | InvoiceOperations | ReportOperations  |
+-------------------------------------------------------------+
|                    MCP Server                                |
|   +-----------+    +------------+    +----------+            |
|   |   Tools   |    | Resources  |    | Prompts  |            |
|   +-----------+    +------------+    +----------+            |
+-------------------------------------------------------------+
|                  Transport Layer                             |
|               +----------+    +----------+                   |
|               |  STDIO   |    |   HTTP   |                   |
|               +----------+    +----------+                   |
+-------------------------------------------------------------+
|                 Infrastructure                               |
|     Database | Repositories | Lock Manager | Config          |
+-------------------------------------------------------------+
```

## Layers

### 1. GUI Layer

Provides user interfaces for direct interaction.

- **CLI**: Command-line interface using Click
- **Web**: Web interface using aiohttp

### 2. SDK Layer

High-level Python API for programmatic access.

- CustomerOperations: Create, update, delete, list customers
- InvoiceOperations: Create invoices, add items, payments
- ReportOperations: Statistics, reports, configuration

### 3. MCP Server Layer

Implements the Model Context Protocol.

- **Tools**: Write operations (create, update, delete)
- **Resources**: Read operations (lists, details, stats)
- **Prompts**: AI model guidance templates

### 4. Transport Layer

Handles communication protocols.

- **STDIO**: For MCP clients like Claude Desktop
- **HTTP/SSE**: For web-based integrations

### 5. Infrastructure Layer

Core services and data access.

- **Database**: SQLite with aiosqlite
- **Repositories**: Data access patterns
- **Lock Manager**: Concurrency control
- **Config**: Environment configuration

## Data Flow

### Tool Execution Flow

```
Client Request
    |
    v
Transport (STDIO/HTTP)
    |
    v
MCP Server (handle_request)
    |
    v
Tool (execute)
    |
    v
Repository (data access)
    |
    v
Database (SQLite)
    |
    v
Response back through layers
```

### Resource Read Flow

```
Client Request
    |
    v
Transport
    |
    v
MCP Server (handle_resources_read)
    |
    v
Resource (read)
    |
    v
Repository
    |
    v
Database
    |
    v
JSON Response
```

## Key Components

### InvoiceMCPServer

Central component that:
- Registers tools, resources, prompts
- Routes MCP protocol messages
- Manages lifecycle

### Repositories

Data access layer:
- CustomerRepository
- InvoiceRepository
- Abstract database operations

### Domain Models

Core business objects:
- Customer
- Invoice
- LineItem
- InvoiceStatus (enum)
- InvoiceType (enum)

## Extension Points

### Adding New Tools

Implement Tool base class with:
- name, description
- input_schema property
- execute() async method

### Adding New Resources

Implement StaticResource or DynamicResource:
- uri, name, description
- read() async method

### Adding New Transports

Implement transport interface:
- start() / stop()
- Message handling

## Configuration

Via environment variables or .env file:

- SERVER_HOST, SERVER_PORT
- DB_PATH
- VAT_RATE, CURRENCY
- TRANSPORT_TYPE
- LOG_LEVEL

---

*Created by AI Agent 3 (Documentation)*
