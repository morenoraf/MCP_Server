"""
Web Interface using FastAPI.

Provides a REST API and simple web interface for invoice management.
All operations go through the SDK layer.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from invoice_mcp_server.sdk.client import InvoiceSDK
from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger

logger = get_logger(__name__)

# Global SDK instance for the web app
_sdk: InvoiceSDK | None = None


class CustomerCreateRequest(BaseModel):
    """Request model for creating a customer."""
    name: str
    email: str
    address: str | None = None
    phone: str | None = None


class CustomerUpdateRequest(BaseModel):
    """Request model for updating a customer."""
    name: str | None = None
    email: str | None = None
    address: str | None = None
    phone: str | None = None


class InvoiceCreateRequest(BaseModel):
    """Request model for creating an invoice."""
    customer_id: str
    due_date: str | None = None
    notes: str | None = None


class InvoiceItemRequest(BaseModel):
    """Request model for adding an invoice item."""
    description: str
    quantity: int
    unit_price: float


class PaymentRequest(BaseModel):
    """Request model for recording a payment."""
    amount: float
    payment_method: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan."""
    global _sdk
    _sdk = InvoiceSDK()
    await _sdk.initialize()
    logger.info("Web application started")
    yield
    await _sdk.shutdown()
    logger.info("Web application stopped")


def create_web_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = Config()

    app = FastAPI(
        title="Invoice MCP Server",
        description="Web interface for Invoice Management",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Invoice MCP Server", "status": "running"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    # Customer endpoints
    @app.get("/api/customers")
    async def list_customers() -> list[dict[str, Any]]:
        """List all customers."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.customers.list_all()

    @app.post("/api/customers")
    async def create_customer(request: CustomerCreateRequest) -> dict[str, Any]:
        """Create a new customer."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.customers.create(
            name=request.name,
            email=request.email,
            address=request.address,
            phone=request.phone,
        )

    @app.delete("/api/customers/{customer_id}")
    async def delete_customer(customer_id: str) -> dict[str, Any]:
        """Delete a customer."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.customers.delete(customer_id)

    # Invoice endpoints
    @app.get("/api/invoices")
    async def list_invoices() -> list[dict[str, Any]]:
        """List all invoices."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.invoices.list_all()

    @app.post("/api/invoices")
    async def create_invoice(request: InvoiceCreateRequest) -> dict[str, Any]:
        """Create a new invoice."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.invoices.create(
            customer_id=request.customer_id,
            due_date=request.due_date,
            notes=request.notes,
        )

    @app.post("/api/invoices/{invoice_id}/items")
    async def add_invoice_item(invoice_id: str, request: InvoiceItemRequest) -> dict[str, Any]:
        """Add an item to an invoice."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.invoices.add_item(
            invoice_id=invoice_id,
            description=request.description,
            quantity=request.quantity,
            unit_price=request.unit_price,
        )

    @app.post("/api/invoices/{invoice_id}/send")
    async def send_invoice(invoice_id: str) -> dict[str, Any]:
        """Send an invoice."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.invoices.send(invoice_id)

    @app.post("/api/invoices/{invoice_id}/payment")
    async def record_payment(invoice_id: str, request: PaymentRequest) -> dict[str, Any]:
        """Record a payment."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.invoices.record_payment(
            invoice_id=invoice_id,
            amount=request.amount,
            payment_method=request.payment_method,
        )

    # Report endpoints
    @app.get("/api/reports/statistics")
    async def get_statistics() -> dict[str, Any]:
        """Get statistics."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.reports.get_statistics()

    @app.get("/api/reports/overdue")
    async def get_overdue_invoices() -> list[dict[str, Any]]:
        """Get overdue invoices."""
        if not _sdk:
            raise HTTPException(status_code=503, detail="SDK not initialized")
        return await _sdk.invoices.get_overdue()

    return app
