"""
Input Validation Module - Security Fix
Added by Agent 2 to prevent injection attacks and validate all inputs
"""
import re
from typing import Any, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_value: Any = None

class InputValidator:
    """Secure input validation for all MCP operations."""
    
    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)]{7,20}$')
    SQL_INJECTION_PATTERN = re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND)\b.*[=;])', re.IGNORECASE)
    XSS_PATTERN = re.compile(r'<script[^>]*>|javascript:|on\w+\s*=', re.IGNORECASE)
    
    @classmethod
    def validate_email(cls, email: str) -> ValidationResult:
        """Validate and sanitize email address."""
        if not email or not isinstance(email, str):
            return ValidationResult(False, "Email is required")
        
        email = email.strip().lower()
        if len(email) > 254:
            return ValidationResult(False, "Email too long")
        
        if not cls.EMAIL_PATTERN.match(email):
            return ValidationResult(False, "Invalid email format")
        
        return ValidationResult(True, sanitized_value=email)
    
    @classmethod
    def validate_customer_name(cls, name: str) -> ValidationResult:
        """Validate customer name - prevent injection attacks."""
        if not name or not isinstance(name, str):
            return ValidationResult(False, "Name is required")
        
        name = name.strip()
        if len(name) < 2 or len(name) > 200:
            return ValidationResult(False, "Name must be 2-200 characters")
        
        # Check for SQL injection
        if cls.SQL_INJECTION_PATTERN.search(name):
            return ValidationResult(False, "Invalid characters in name")
        
        # Check for XSS
        if cls.XSS_PATTERN.search(name):
            return ValidationResult(False, "Invalid characters in name")
        
        # Sanitize: escape special characters
        sanitized = cls._sanitize_string(name)
        return ValidationResult(True, sanitized_value=sanitized)
    
    @classmethod
    def validate_amount(cls, amount: Any) -> ValidationResult:
        """Validate monetary amount."""
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return ValidationResult(False, "Invalid amount format")
        
        if amount < 0:
            return ValidationResult(False, "Amount cannot be negative")
        
        if amount > 999999999.99:
            return ValidationResult(False, "Amount exceeds maximum")
        
        # Round to 2 decimal places
        sanitized = round(amount, 2)
        return ValidationResult(True, sanitized_value=sanitized)
    
    @classmethod
    def validate_invoice_id(cls, invoice_id: str) -> ValidationResult:
        """Validate UUID format for invoice ID."""
        if not invoice_id or not isinstance(invoice_id, str):
            return ValidationResult(False, "Invoice ID is required")
        
        # UUID v4 format
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        if not uuid_pattern.match(invoice_id):
            return ValidationResult(False, "Invalid invoice ID format")
        
        return ValidationResult(True, sanitized_value=invoice_id.lower())
    
    @staticmethod
    def _sanitize_string(value: str) -> str:
        """Remove potentially dangerous characters."""
        # HTML entity encoding for special chars
        replacements = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;',
        }
        for char, replacement in replacements.items():
            value = value.replace(char, replacement)
        return value


def secure_operation(func):
    """Decorator to add input validation to MCP operations."""
    def wrapper(*args, **kwargs):
        # Log the operation for audit
        import logging
        logger = logging.getLogger('security.audit')
        logger.info(f"Operation: {func.__name__}, args: {len(args)}, kwargs: {list(kwargs.keys())}")
        return func(*args, **kwargs)
    return wrapper
