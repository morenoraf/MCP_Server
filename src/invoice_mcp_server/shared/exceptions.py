"""
Custom exception hierarchy for the Invoice MCP Server.

Provides structured error handling with:
    - Clear error categories
    - Error codes for programmatic handling
    - Detailed error messages
    - Support for error chaining
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(Enum):
    """Enumeration of error codes for programmatic handling."""

    # General errors (1000-1999)
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    CONFIGURATION_ERROR = 1002

    # Resource errors (2000-2999)
    NOT_FOUND = 2000
    ALREADY_EXISTS = 2001
    RESOURCE_LOCKED = 2002

    # Business logic errors (3000-3999)
    INVALID_INVOICE_STATE = 3000
    PAYMENT_ERROR = 3001
    CALCULATION_ERROR = 3002

    # Storage errors (4000-4999)
    DATABASE_ERROR = 4000
    CONNECTION_ERROR = 4001
    TRANSACTION_ERROR = 4002

    # Transport errors (5000-5999)
    TRANSPORT_ERROR = 5000
    PROTOCOL_ERROR = 5001
    TIMEOUT_ERROR = 5002

    # MCP errors (6000-6999)
    TOOL_NOT_FOUND = 6000
    RESOURCE_NOT_FOUND = 6001
    INVALID_PARAMS = 6002


class InvoiceError(Exception):
    """
    Base exception for all Invoice MCP Server errors.

    Attributes:
        message: Human-readable error message
        code: Error code for programmatic handling
        details: Additional error context
        cause: Original exception if this wraps another error
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize the exception with message and optional details."""
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code.value,
            "code_name": self.code.name,
            "details": self.details,
        }

    def __str__(self) -> str:
        """Return string representation of the error."""
        base = f"[{self.code.name}] {self.message}"
        if self.details:
            base += f" - Details: {self.details}"
        if self.cause:
            base += f" - Caused by: {self.cause}"
        return base


class ValidationError(InvoiceError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error with field information."""
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            details=details,
        )
        self.field = field
        self.value = value


class NotFoundError(InvoiceError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize not found error with resource information."""
        details = details or {}
        details["resource_type"] = resource_type
        details["resource_id"] = resource_id

        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            code=ErrorCode.NOT_FOUND,
            details=details,
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class AlreadyExistsError(InvoiceError):
    """Raised when trying to create a resource that already exists."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize already exists error."""
        details = details or {}
        details["resource_type"] = resource_type
        details["resource_id"] = resource_id

        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' already exists",
            code=ErrorCode.ALREADY_EXISTS,
            details=details,
        )


class DatabaseError(InvoiceError):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize database error."""
        details: dict[str, Any] = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            code=ErrorCode.DATABASE_ERROR,
            details=details,
            cause=cause,
        )


class TransportError(InvoiceError):
    """Raised when a transport layer operation fails."""

    def __init__(
        self,
        message: str,
        transport_type: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize transport error."""
        details: dict[str, Any] = {}
        if transport_type:
            details["transport_type"] = transport_type

        super().__init__(
            message=message,
            code=ErrorCode.TRANSPORT_ERROR,
            details=details,
            cause=cause,
        )


class MCPError(InvoiceError):
    """Raised when an MCP protocol error occurs."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.PROTOCOL_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize MCP error."""
        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class BusinessLogicError(InvoiceError):
    """Raised when a business rule is violated."""

    def __init__(
        self,
        message: str,
        rule: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize business logic error."""
        details = details or {}
        if rule:
            details["rule"] = rule

        super().__init__(
            message=message,
            code=ErrorCode.INVALID_INVOICE_STATE,
            details=details,
        )
