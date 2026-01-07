"""
CLI Interface using Click.

Provides a command-line interface for invoice management.
All operations go through the SDK layer.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import click

from invoice_mcp_server.sdk.client import InvoiceSDK


def run_async(coro: Any) -> Any:
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


@click.group()
@click.pass_context
def cli_app(ctx: click.Context) -> None:
    """Invoice MCP Server CLI - Manage invoices and customers."""
    ctx.ensure_object(dict)


@cli_app.group()
def customer() -> None:
    """Customer management commands."""
    pass


@customer.command("create")
@click.option("--name", "-n", required=True, help="Customer name")
@click.option("--email", "-e", required=True, help="Customer email")
@click.option("--address", "-a", help="Customer address")
@click.option("--phone", "-p", help="Customer phone")
def customer_create(name: str, email: str, address: str | None, phone: str | None) -> None:
    """Create a new customer."""
    async def _create() -> None:
        async with InvoiceSDK() as sdk:
            result = await sdk.customers.create(name, email, address, phone)
            click.echo(json.dumps(result, indent=2, default=str))

    run_async(_create())


@customer.command("list")
def customer_list() -> None:
    """List all customers."""
    async def _list() -> None:
        async with InvoiceSDK() as sdk:
            customers = await sdk.customers.list_all()
            if not customers:
                click.echo("No customers found.")
                return
            for c in customers:
                click.echo(f"  {c.get('id', 'N/A')}: {c.get('name', 'N/A')} <{c.get('email', 'N/A')}>")

    run_async(_list())


@customer.command("delete")
@click.argument("customer_id")
def customer_delete(customer_id: str) -> None:
    """Delete a customer by ID."""
    async def _delete() -> None:
        async with InvoiceSDK() as sdk:
            result = await sdk.customers.delete(customer_id)
            click.echo(json.dumps(result, indent=2, default=str))

    run_async(_delete())


@cli_app.group()
def invoice() -> None:
    """Invoice management commands."""
    pass


@invoice.command("create")
@click.option("--customer-id", "-c", required=True, help="Customer ID")
@click.option("--due-date", "-d", help="Due date (YYYY-MM-DD)")
@click.option("--notes", "-n", help="Invoice notes")
def invoice_create(customer_id: str, due_date: str | None, notes: str | None) -> None:
    """Create a new invoice."""
    async def _create() -> None:
        async with InvoiceSDK() as sdk:
            result = await sdk.invoices.create(customer_id, due_date, notes)
            click.echo(json.dumps(result, indent=2, default=str))

    run_async(_create())


@invoice.command("add-item")
@click.option("--invoice-id", "-i", required=True, help="Invoice ID")
@click.option("--description", "-d", required=True, help="Item description")
@click.option("--quantity", "-q", type=int, required=True, help="Quantity")
@click.option("--price", "-p", type=float, required=True, help="Unit price")
def invoice_add_item(invoice_id: str, description: str, quantity: int, price: float) -> None:
    """Add an item to an invoice."""
    async def _add() -> None:
        async with InvoiceSDK() as sdk:
            result = await sdk.invoices.add_item(invoice_id, description, quantity, price)
            click.echo(json.dumps(result, indent=2, default=str))

    run_async(_add())


@invoice.command("list")
def invoice_list() -> None:
    """List all invoices."""
    async def _list() -> None:
        async with InvoiceSDK() as sdk:
            invoices = await sdk.invoices.list_all()
            if not invoices:
                click.echo("No invoices found.")
                return
            for inv in invoices:
                status = inv.get("status", "unknown")
                total = inv.get("total", 0)
                click.echo(f"  {inv.get('invoice_number', 'N/A')}: {status} - {total}")

    run_async(_list())


@invoice.command("send")
@click.argument("invoice_id")
def invoice_send(invoice_id: str) -> None:
    """Send an invoice to the customer."""
    async def _send() -> None:
        async with InvoiceSDK() as sdk:
            result = await sdk.invoices.send(invoice_id)
            click.echo(json.dumps(result, indent=2, default=str))

    run_async(_send())


@invoice.command("pay")
@click.option("--invoice-id", "-i", required=True, help="Invoice ID")
@click.option("--amount", "-a", type=float, required=True, help="Payment amount")
@click.option("--method", "-m", required=True, help="Payment method")
def invoice_pay(invoice_id: str, amount: float, method: str) -> None:
    """Record a payment for an invoice."""
    async def _pay() -> None:
        async with InvoiceSDK() as sdk:
            result = await sdk.invoices.record_payment(invoice_id, amount, method)
            click.echo(json.dumps(result, indent=2, default=str))

    run_async(_pay())


@cli_app.group()
def report() -> None:
    """Reporting commands."""
    pass


@report.command("stats")
def report_stats() -> None:
    """Show overall statistics."""
    async def _stats() -> None:
        async with InvoiceSDK() as sdk:
            stats = await sdk.reports.get_statistics()
            click.echo(json.dumps(stats, indent=2, default=str))

    run_async(_stats())


@report.command("overdue")
def report_overdue() -> None:
    """Show overdue invoices."""
    async def _overdue() -> None:
        async with InvoiceSDK() as sdk:
            invoices = await sdk.invoices.get_overdue()
            if not invoices:
                click.echo("No overdue invoices.")
                return
            for inv in invoices:
                click.echo(f"  {inv.get('invoice_number')}: {inv.get('total')} (due: {inv.get('due_date')})")

    run_async(_overdue())


def main() -> None:
    """Main entry point for CLI."""
    cli_app()


if __name__ == "__main__":
    main()
