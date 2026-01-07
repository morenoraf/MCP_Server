"""
Unit tests for SDK module.

Tests SDK client and operations through the SDK layer.
"""

from __future__ import annotations

import pytest

from invoice_mcp_server.sdk.client import InvoiceSDK
from invoice_mcp_server.sdk.operations import (
    CustomerOperations,
    InvoiceOperations,
    ReportOperations,
)


class TestInvoiceSDK:
    """Tests for InvoiceSDK class."""

    @pytest.mark.asyncio
    async def test_initialization(self, config_with_temp_db) -> None:
        """Test SDK initialization."""
        sdk = InvoiceSDK()
        await sdk.initialize()

        assert sdk._initialized is True
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_context_manager(self, config_with_temp_db) -> None:
        """Test SDK context manager."""
        async with InvoiceSDK() as sdk:
            assert sdk._initialized is True

    @pytest.mark.asyncio
    async def test_customers_property(self, config_with_temp_db) -> None:
        """Test customers property returns CustomerOperations."""
        async with InvoiceSDK() as sdk:
            assert isinstance(sdk.customers, CustomerOperations)

    @pytest.mark.asyncio
    async def test_invoices_property(self, config_with_temp_db) -> None:
        """Test invoices property returns InvoiceOperations."""
        async with InvoiceSDK() as sdk:
            assert isinstance(sdk.invoices, InvoiceOperations)

    @pytest.mark.asyncio
    async def test_reports_property(self, config_with_temp_db) -> None:
        """Test reports property returns ReportOperations."""
        async with InvoiceSDK() as sdk:
            assert isinstance(sdk.reports, ReportOperations)

    @pytest.mark.asyncio
    async def test_request_id_increment(self, config_with_temp_db) -> None:
        """Test request ID increments."""
        async with InvoiceSDK() as sdk:
            id1 = sdk._next_request_id()
            id2 = sdk._next_request_id()
            assert id2 == id1 + 1

    @pytest.mark.asyncio
    async def test_shutdown(self, config_with_temp_db) -> None:
        """Test SDK shutdown."""
        sdk = InvoiceSDK()
        await sdk.initialize()
        await sdk.shutdown()

        assert sdk._initialized is False


class TestCustomerOperations:
    """Tests for CustomerOperations class."""

    @pytest.mark.asyncio
    async def test_create_customer(self, config_with_temp_db) -> None:
        """Test creating a customer through SDK."""
        async with InvoiceSDK() as sdk:
            result = await sdk.customers.create(
                name="SDK Test Customer",
                email="sdk@example.com",
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_list_customers(self, config_with_temp_db) -> None:
        """Test listing customers through SDK."""
        async with InvoiceSDK() as sdk:
            # Create a customer first
            await sdk.customers.create(
                name="List Test",
                email="list@example.com",
            )

            customers = await sdk.customers.list_all()
            assert isinstance(customers, list)


class TestInvoiceOperations:
    """Tests for InvoiceOperations class."""

    @pytest.mark.asyncio
    async def test_create_invoice(self, config_with_temp_db) -> None:
        """Test creating an invoice through SDK."""
        async with InvoiceSDK() as sdk:
            # Create a customer first
            await sdk.customers.create(
                name="Invoice Customer",
                email="invoice@example.com",
            )

            customers = await sdk.customers.list_all()
            if customers:
                customer_id = customers[0].get("id")
                result = await sdk.invoices.create(customer_id=customer_id)
                assert result is not None

    @pytest.mark.asyncio
    async def test_list_invoices(self, config_with_temp_db) -> None:
        """Test listing invoices through SDK."""
        async with InvoiceSDK() as sdk:
            invoices = await sdk.invoices.list_all()
            assert isinstance(invoices, list)


class TestReportOperations:
    """Tests for ReportOperations class."""

    @pytest.mark.asyncio
    async def test_get_statistics(self, config_with_temp_db) -> None:
        """Test getting statistics through SDK."""
        async with InvoiceSDK() as sdk:
            stats = await sdk.reports.get_statistics()
            assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_get_config(self, config_with_temp_db) -> None:
        """Test getting config through SDK."""
        async with InvoiceSDK() as sdk:
            config = await sdk.reports.get_config()
            assert isinstance(config, dict)
