"""
Authentication Middleware Module - Security Enhancement.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from invoice_mcp_server.shared.logging import get_logger

logger = get_logger(__name__)


class AuthResult(Enum):
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    EXPIRED_TOKEN = "expired_token"
    MISSING_CREDENTIALS = "missing_credentials"
    RATE_LIMITED = "rate_limited"


@dataclass
class AuthContext:
    result: AuthResult
    client_id: Optional[str] = None
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return self.result == AuthResult.SUCCESS


@dataclass
class APIKey:
    key_id: str
    key_hash: str
    client_id: str
    permissions: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    is_active: bool = True

    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and time.time() > self.expires_at:
            return False
        return True


class AuthenticationStrategy(ABC):
    @abstractmethod
    def authenticate(self, credentials: dict[str, Any]) -> AuthContext:
        pass

    @abstractmethod
    def get_header_name(self) -> str:
        pass


class APIKeyAuthentication(AuthenticationStrategy):
    def __init__(self) -> None:
        self._keys: dict[str, APIKey] = {}
        self._header_name = os.getenv("AUTH_HEADER", "X-API-Key")

    def get_header_name(self) -> str:
        return self._header_name

    @staticmethod
    def _hash_key(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    def generate_key(self, client_id: str, permissions: Optional[list[str]] = None, expires_in_seconds: Optional[int] = None) -> tuple[str, str]:
        key_id = f"key_{secrets.token_hex(8)}"
        secret_key = secrets.token_urlsafe(32)
        key_hash = self._hash_key(secret_key)
        expires_at = time.time() + expires_in_seconds if expires_in_seconds else None
        api_key = APIKey(key_id=key_id, key_hash=key_hash, client_id=client_id, permissions=permissions or [], expires_at=expires_at)
        self._keys[key_id] = api_key
        logger.info(f"Generated API key {key_id} for client {client_id}")
        return key_id, secret_key

    def register_key(self, key_id: str, key_hash: str, client_id: str, permissions: Optional[list[str]] = None) -> None:
        api_key = APIKey(key_id=key_id, key_hash=key_hash, client_id=client_id, permissions=permissions or [])
        self._keys[key_id] = api_key

    def revoke_key(self, key_id: str) -> bool:
        if key_id in self._keys:
            self._keys[key_id].is_active = False
            return True
        return False

    def authenticate(self, credentials: dict[str, Any]) -> AuthContext:
        api_key = credentials.get("api_key")
        if not api_key:
            return AuthContext(result=AuthResult.MISSING_CREDENTIALS, metadata={"error": "API key not provided"})
        key_hash = self._hash_key(api_key)
        for key_id, stored_key in self._keys.items():
            if hmac.compare_digest(stored_key.key_hash, key_hash):
                if not stored_key.is_valid():
                    if not stored_key.is_active:
                        return AuthContext(result=AuthResult.INVALID_CREDENTIALS, metadata={"error": "API key revoked"})
                    return AuthContext(result=AuthResult.EXPIRED_TOKEN, metadata={"error": "API key expired"})
                return AuthContext(result=AuthResult.SUCCESS, client_id=stored_key.client_id, permissions=stored_key.permissions.copy(), metadata={"key_id": key_id})
        return AuthContext(result=AuthResult.INVALID_CREDENTIALS, metadata={"error": "Invalid API key"})


class BearerTokenAuthentication(AuthenticationStrategy):
    def __init__(self, secret_key: Optional[str] = None) -> None:
        self._secret_key = secret_key or os.getenv("AUTH_SECRET_KEY", secrets.token_hex(32))
        self._header_name = "Authorization"
        self._tokens: dict[str, dict[str, Any]] = {}

    def get_header_name(self) -> str:
        return self._header_name

    def generate_token(self, client_id: str, permissions: Optional[list[str]] = None, expires_in_seconds: int = 3600) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self._tokens[token_hash] = {"client_id": client_id, "permissions": permissions or [], "created_at": time.time(), "expires_at": time.time() + expires_in_seconds}
        return token

    def revoke_token(self, token: str) -> bool:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in self._tokens:
            del self._tokens[token_hash]
            return True
        return False

    def authenticate(self, credentials: dict[str, Any]) -> AuthContext:
        token = credentials.get("token", "")
        if not token:
            return AuthContext(result=AuthResult.MISSING_CREDENTIALS, metadata={"error": "Token not provided"})
        if token.startswith("Bearer "):
            token = token[7:]
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash not in self._tokens:
            return AuthContext(result=AuthResult.INVALID_CREDENTIALS, metadata={"error": "Invalid token"})
        token_data = self._tokens[token_hash]
        if time.time() > token_data["expires_at"]:
            del self._tokens[token_hash]
            return AuthContext(result=AuthResult.EXPIRED_TOKEN, metadata={"error": "Token expired"})
        return AuthContext(result=AuthResult.SUCCESS, client_id=token_data["client_id"], permissions=token_data["permissions"])


class AuthManager:
    def __init__(self) -> None:
        self._strategies: dict[str, AuthenticationStrategy] = {}
        self._default_strategy: Optional[str] = None

    def register_strategy(self, name: str, strategy: AuthenticationStrategy, set_default: bool = False) -> None:
        self._strategies[name] = strategy
        if set_default or self._default_strategy is None:
            self._default_strategy = name

    def authenticate(self, credentials: dict[str, Any], strategy_name: Optional[str] = None) -> AuthContext:
        strategy_name = strategy_name or self._default_strategy
        if not strategy_name or strategy_name not in self._strategies:
            return AuthContext(result=AuthResult.MISSING_CREDENTIALS, metadata={"error": "No auth strategy"})
        return self._strategies[strategy_name].authenticate(credentials)

    def get_strategy(self, name: str) -> Optional[AuthenticationStrategy]:
        return self._strategies.get(name)


_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
        if os.getenv("AUTH_API_KEY_ENABLED", "true").lower() == "true":
            api_key_auth = APIKeyAuthentication()
            _auth_manager.register_strategy("api_key", api_key_auth, set_default=True)
            env_key = os.getenv("AUTH_API_KEY")
            if env_key:
                key_hash = APIKeyAuthentication._hash_key(env_key)
                api_key_auth.register_key(key_id="env_key", key_hash=key_hash, client_id=os.getenv("AUTH_CLIENT_ID", "default"), permissions=["read", "write"])
        if os.getenv("AUTH_BEARER_ENABLED", "false").lower() == "true":
            _auth_manager.register_strategy("bearer", BearerTokenAuthentication())
    return _auth_manager


def reset_auth_manager() -> None:
    global _auth_manager
    _auth_manager = None


F = TypeVar("F", bound=Callable[..., Any])


def require_auth(permissions: Optional[list[str]] = None) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            auth_context = kwargs.get("auth_context")
            if not auth_context or not auth_context.is_authenticated:
                from aiohttp import web
                return web.json_response({"error": "Authentication required"}, status=401)
            if permissions:
                missing = set(permissions) - set(auth_context.permissions)
                if missing:
                    from aiohttp import web
                    return web.json_response({"error": f"Missing: {missing}"}, status=403)
            return await func(*args, **kwargs)
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            auth_context = kwargs.get("auth_context")
            if not auth_context or not auth_context.is_authenticated:
                raise PermissionError("Authentication required")
            if permissions:
                missing = set(permissions) - set(auth_context.permissions)
                if missing:
                    raise PermissionError(f"Missing: {missing}")
            return func(*args, **kwargs)
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


async def auth_middleware(request: Any, handler: Callable[..., Any]) -> Any:
    from aiohttp import web
    if request.path == "/health" or request.method == "OPTIONS":
        return await handler(request)
    auth_required = os.getenv("AUTH_REQUIRED", "false").lower() == "true"
    if not auth_required:
        request["auth_context"] = AuthContext(result=AuthResult.SUCCESS)
        return await handler(request)
    auth_manager = get_auth_manager()
    api_key_strategy = auth_manager.get_strategy("api_key")
    if api_key_strategy:
        api_key = request.headers.get(api_key_strategy.get_header_name())
        if api_key:
            auth_context = auth_manager.authenticate({"api_key": api_key}, strategy_name="api_key")
            if auth_context.is_authenticated:
                request["auth_context"] = auth_context
                return await handler(request)
    bearer_strategy = auth_manager.get_strategy("bearer")
    if bearer_strategy:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            auth_context = auth_manager.authenticate({"token": auth_header}, strategy_name="bearer")
            if auth_context.is_authenticated:
                request["auth_context"] = auth_context
                return await handler(request)
    return web.json_response({"error": "Authentication required"}, status=401)
