"""
Unit tests for exception module.

Tests custom exceptions, error codes, and serialization.
"""

from __future__ import annotations

import pytest

from invoice_mcp_server.shared.exceptions import (
    ErrorCode,
    InvoiceError,
    ValidationError,
    NotFoundError,
    AlreadyExistsError,
    DatabaseError,
    TransportError,
    MCPError,
    BusinessLogicError,
)


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_all_codes_unique(self) -> None:
        """Test that all error codes are unique."""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values))

    def test_code_ranges(self) -> None:
        """Test error codes are in correct ranges."""
        assert 1000 <= ErrorCode.VALIDATION_ERROR.value < 2000
        assert 2000 <= ErrorCode.NOT_FOUND.value < 3000
        assert 3000 <= ErrorCode.INVALID_INVOICE_STATE.value < 4000
        assert 4000 <= ErrorCode.DATABASE_ERROR.value < 5000
        assert 5000 <= ErrorCode.TRANSPORT_ERROR.value < 6000
        assert 6000 <= ErrorCode.TOOL_NOT_FOUND.value < 7000


class TestInvoiceError:
    """Tests for base InvoiceError."""

    def test_basic_creation(self) -> None:
        """Test basic error creation."""
        error = InvoiceError("Test error")
        assert error.message == "Test error"
        assert error.code == ErrorCode.UNKNOWN_ERROR

    def test_with_code(self) -> None:
        """Test error with specific code."""
        error = InvoiceError("Test", code=ErrorCode.VALIDATION_ERROR)
        assert error.code == ErrorCode.VALIDATION_ERROR

    def test_with_details(self) -> None:
        """Test error with details."""
        error = InvoiceError("Test", details={"key": "value"})
        assert error.details["key"] == "value"

    def test_with_cause(self) -> None:
        """Test error with cause."""
        cause = ValueError("Original error")
        error = InvoiceError("Test", cause=cause)
        assert error.cause is cause

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        error = InvoiceError(
            "Test error",
            code=ErrorCode.VALIDATION_ERROR,
            details={"field": "name"},
        )
        data = error.to_dict()

        assert data["error"] == "InvoiceError"
        assert data["message"] == "Test error"
        assert data["code"] == ErrorCode.VALIDATION_ERROR.value
        assert data["code_name"] == "VALIDATION_ERROR"
        assert data["details"]["field"] == "name"

    def test_str_representation(self) -> None:
        """Test string representation."""
        error = InvoiceError("Test error", code=ErrorCode.VALIDATION_ERROR)
        str_repr = str(error)
        assert "VALIDATION_ERROR" in str_repr
        assert "Test error" in str_repr


class TestValidationError:
    """Tests for ValidationError."""

    def test_basic_creation(self) -> None:
        """Test basic validation error."""
        error = ValidationError("Invalid value")
        assert error.code == ErrorCode.VALIDATION_ERROR

    def test_with_field(self) -> None:
        """Test validation error with field."""
        error = ValidationError("Invalid email", field="email")
        assert error.field == "email"
        assert error.details["field"] == "email"

    def test_with_value(self) -> None:
        """Test validation error with value."""
        error = ValidationError("Invalid", field="count", value=123)
        assert error.value == 123
        assert error.details["value"] == "123"


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_basic_creation(self) -> None:
        """Test basic not found error."""
        error = NotFoundError("Customer", "CUST-001")
        assert error.code == ErrorCode.NOT_FOUND
        assert "Customer" in error.message
        assert "CUST-001" in error.message

    def test_details(self) -> None:
        """Test not found error details."""
        error = NotFoundError("Invoice", "INV-001")
        assert error.resource_type == "Invoice"
        assert error.resource_id == "INV-001"


class TestAlreadyExistsError:
    """Tests for AlreadyExistsError."""

    def test_basic_creation(self) -> None:
        """Test basic already exists error."""
        error = AlreadyExistsError("Customer", "CUST-001")
        assert error.code == ErrorCode.ALREADY_EXISTS
        assert "already exists" in error.message


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_basic_creation(self) -> None:
        """Test basic database error."""
        error = DatabaseError("Connection failed")
        assert error.code == ErrorCode.DATABASE_ERROR

    def test_with_operation(self) -> None:
        """Test database error with operation."""
        error = DatabaseError("Failed", operation="INSERT")
        assert error.details["operation"] == "INSERT"

    def test_with_cause(self) -> None:
        """Test database error with cause."""
        cause = Exception("Original")
        error = DatabaseError("Failed", cause=cause)
        assert error.cause is cause


class TestTransportError:
    """Tests for TransportError."""

    def test_basic_creation(self) -> None:
        """Test basic transport error."""
        error = TransportError("Connection refused")
        assert error.code == ErrorCode.TRANSPORT_ERROR

    def test_with_transport_type(self) -> None:
        """Test transport error with type."""
        error = TransportError("Failed", transport_type="http")
        assert error.details["transport_type"] == "http"


class TestMCPError:
    """Tests for MCPError."""

    def test_basic_creation(self) -> None:
        """Test basic MCP error."""
        error = MCPError("Protocol error")
        assert error.code == ErrorCode.PROTOCOL_ERROR

    def test_with_custom_code(self) -> None:
        """Test MCP error with custom code."""
        error = MCPError("Tool not found", code=ErrorCode.TOOL_NOT_FOUND)
        assert error.code == ErrorCode.TOOL_NOT_FOUND


class TestBusinessLogicError:
    """Tests for BusinessLogicError."""

    def test_basic_creation(self) -> None:
        """Test basic business logic error."""
        error = BusinessLogicError("Cannot void paid invoice")
        assert error.code == ErrorCode.INVALID_INVOICE_STATE

    def test_with_rule(self) -> None:
        """Test business logic error with rule."""
        error = BusinessLogicError("Failed", rule="PAYMENT_REQUIRED")
        assert error.details["rule"] == "PAYMENT_REQUIRED"
