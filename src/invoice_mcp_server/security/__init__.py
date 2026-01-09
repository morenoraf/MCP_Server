"""
Security Module - Comprehensive Security Features for Invoice MCP Server.

This module provides:
    - Input validation and sanitization
    - Authentication middleware with API key and token support
    - Rate limiting to protect against abuse
    - Audit logging for tracking operations

Usage:
    from invoice_mcp_server.security import (
        InputValidator,
        get_auth_manager,
        auth_middleware,
        get_rate_limiter,
        rate_limit_middleware,
        get_audit_logger,
        audit_middleware,
    )
"""

from invoice_mcp_server.security.input_validator import (
    InputValidator,
    ValidationResult,
    secure_operation,
)

from invoice_mcp_server.security.auth import (
    AuthResult,
    AuthContext,
    APIKey,
    AuthenticationStrategy,
    APIKeyAuthentication,
    BearerTokenAuthentication,
    AuthManager,
    get_auth_manager,
    reset_auth_manager,
    require_auth,
    auth_middleware,
)

from invoice_mcp_server.security.rate_limiter import (
    RateLimitResult,
    RateLimitConfig,
    RateLimitResponse,
    RateLimiter,
    get_rate_limiter,
    reset_rate_limiter,
    rate_limit,
    rate_limit_middleware,
)

from invoice_mcp_server.security.audit import (
    AuditAction,
    AuditStatus,
    AuditEntry,
    AuditLogConfig,
    AuditLogger,
    get_audit_logger,
    reset_audit_logger,
    audit,
    audit_middleware,
)

__all__ = [
    # Input validation
    "InputValidator",
    "ValidationResult",
    "secure_operation",
    # Authentication
    "AuthResult",
    "AuthContext",
    "APIKey",
    "AuthenticationStrategy",
    "APIKeyAuthentication",
    "BearerTokenAuthentication",
    "AuthManager",
    "get_auth_manager",
    "reset_auth_manager",
    "require_auth",
    "auth_middleware",
    # Rate limiting
    "RateLimitResult",
    "RateLimitConfig",
    "RateLimitResponse",
    "RateLimiter",
    "get_rate_limiter",
    "reset_rate_limiter",
    "rate_limit",
    "rate_limit_middleware",
    # Audit logging
    "AuditAction",
    "AuditStatus",
    "AuditEntry",
    "AuditLogConfig",
    "AuditLogger",
    "get_audit_logger",
    "reset_audit_logger",
    "audit",
    "audit_middleware",
]
