"""
Audit Logging Module - Security Enhancement.

Provides comprehensive audit logging to track all operations with:
    - Structured audit log entries
    - File logging with rotation support
    - Configurable log formats and destinations
    - Operation tracking (who did what and when)
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Optional

import logging

from invoice_mcp_server.shared.logging import get_logger

logger = get_logger(__name__)


class AuditAction(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_DENIED = "access_denied"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    CUSTOM = "custom"


class AuditStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


@dataclass
class AuditEntry:
    action: AuditAction
    resource_type: str
    timestamp: float = field(default_factory=time.time)
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    client_id: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: AuditStatus = AuditStatus.SUCCESS
    details: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["action"] = self.action.value
        data["status"] = self.status.value
        data["timestamp_iso"] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class AuditLogConfig:
    enabled: bool = field(default_factory=lambda: os.getenv("AUDIT_ENABLED", "true").lower() == "true")
    log_file: Optional[str] = field(default_factory=lambda: os.getenv("AUDIT_LOG_FILE", "logs/audit.log"))
    max_bytes: int = field(default_factory=lambda: int(os.getenv("AUDIT_MAX_BYTES", "10485760")))
    backup_count: int = field(default_factory=lambda: int(os.getenv("AUDIT_BACKUP_COUNT", "10")))
    log_to_console: bool = field(default_factory=lambda: os.getenv("AUDIT_LOG_CONSOLE", "false").lower() == "true")
    log_format: str = field(default_factory=lambda: os.getenv("AUDIT_FORMAT", "json"))


class AuditLogger:
    def __init__(self, config: Optional[AuditLogConfig] = None) -> None:
        self._config = config or AuditLogConfig()
        self._lock = Lock()
        self._logger: Optional[logging.Logger] = None
        self._entries: list[AuditEntry] = []
        self._max_memory_entries = 1000
        if self._config.enabled:
            self._setup_logger()

    def _setup_logger(self) -> None:
        self._logger = logging.getLogger("audit")
        self._logger.setLevel(logging.INFO)
        self._logger.handlers.clear()
        if self._config.log_file:
            log_path = Path(self._config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=self._config.max_bytes,
                backupCount=self._config.backup_count,
            )
            if self._config.log_format == "json":
                file_handler.setFormatter(logging.Formatter("%(message)s"))
            else:
                file_handler.setFormatter(logging.Formatter(
                    "%(asctime)s - %(levelname)s - %(message)s"
                ))
            self._logger.addHandler(file_handler)
        if self._config.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                "[AUDIT] %(asctime)s - %(message)s"
            ))
            self._logger.addHandler(console_handler)
        logger.info("Audit logger initialized")

    def log(self, entry: AuditEntry) -> None:
        if not self._config.enabled:
            return
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max_memory_entries:
                self._entries = self._entries[-self._max_memory_entries:]
            if self._logger:
                if self._config.log_format == "json":
                    self._logger.info(entry.to_json())
                else:
                    msg = (
                        f"[{entry.status.value.upper()}] {entry.action.value} "
                        f"{entry.resource_type}"
                    )
                    if entry.resource_id:
                        msg += f"/{entry.resource_id}"
                    if entry.client_id:
                        msg += f" by {entry.client_id}"
                    if entry.ip_address:
                        msg += f" from {entry.ip_address}"
                    if entry.error_message:
                        msg += f" - Error: {entry.error_message}"
                    self._logger.info(msg)

    def log_action(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        client_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        status: AuditStatus = AuditStatus.SUCCESS,
        details: Optional[dict[str, Any]] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> str:
        entry = AuditEntry(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            client_id=client_id,
            ip_address=ip_address,
            status=status,
            details=details or {},
            error_message=error_message,
            duration_ms=duration_ms,
        )
        self.log(entry)
        return entry.entry_id

    def get_entries(
        self,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        client_id: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        with self._lock:
            entries = self._entries.copy()
        if action:
            entries = [e for e in entries if e.action == action]
        if resource_type:
            entries = [e for e in entries if e.resource_type == resource_type]
        if client_id:
            entries = [e for e in entries if e.client_id == client_id]
        if status:
            entries = [e for e in entries if e.status == status]
        if since:
            entries = [e for e in entries if e.timestamp >= since]
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    def clear_entries(self) -> int:
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count


_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def reset_audit_logger() -> None:
    global _audit_logger
    _audit_logger = None


def audit(
    action: AuditAction,
    resource_type: str,
    get_resource_id: Optional[Callable[..., Optional[str]]] = None,
    get_client_id: Optional[Callable[..., Optional[str]]] = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            audit_logger = get_audit_logger()
            resource_id = None
            client_id = None
            ip_address = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(*args, **kwargs)
                except Exception:
                    pass
            if get_client_id:
                try:
                    client_id = get_client_id(*args, **kwargs)
                except Exception:
                    pass
            request = args[0] if args else kwargs.get("request")
            if hasattr(request, "remote"):
                ip_address = request.remote
            elif hasattr(request, "headers"):
                ip_address = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP"))
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                audit_logger.log_action(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    client_id=client_id,
                    ip_address=ip_address,
                    status=AuditStatus.SUCCESS,
                    duration_ms=duration_ms,
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                audit_logger.log_action(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    client_id=client_id,
                    ip_address=ip_address,
                    status=AuditStatus.FAILURE,
                    error_message=str(e),
                    duration_ms=duration_ms,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            audit_logger = get_audit_logger()
            resource_id = get_resource_id(*args, **kwargs) if get_resource_id else None
            client_id = get_client_id(*args, **kwargs) if get_client_id else None
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                audit_logger.log_action(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    client_id=client_id,
                    status=AuditStatus.SUCCESS,
                    duration_ms=duration_ms,
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                audit_logger.log_action(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    client_id=client_id,
                    status=AuditStatus.FAILURE,
                    error_message=str(e),
                    duration_ms=duration_ms,
                )
                raise

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


async def audit_middleware(request: Any, handler: Callable[..., Any]) -> Any:
    audit_enabled = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
    if not audit_enabled:
        return await handler(request)
    audit_logger = get_audit_logger()
    start_time = time.time()
    client_id = None
    if hasattr(request, "get") and request.get("auth_context"):
        auth_context = request["auth_context"]
        client_id = getattr(auth_context, "client_id", None)
    ip_address = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.remote))
    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()
    user_agent = request.headers.get("User-Agent")
    try:
        response = await handler(request)
        duration_ms = (time.time() - start_time) * 1000
        status = AuditStatus.SUCCESS if response.status < 400 else AuditStatus.FAILURE
        audit_logger.log(AuditEntry(
            action=AuditAction.CUSTOM,
            resource_type="http_request",
            resource_id=request.path,
            client_id=client_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details={
                "method": request.method,
                "path": request.path,
                "status_code": response.status,
            },
            duration_ms=duration_ms,
        ))
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        audit_logger.log(AuditEntry(
            action=AuditAction.ERROR,
            resource_type="http_request",
            resource_id=request.path,
            client_id=client_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=AuditStatus.FAILURE,
            details={
                "method": request.method,
                "path": request.path,
            },
            error_message=str(e),
            duration_ms=duration_ms,
        ))
        raise
