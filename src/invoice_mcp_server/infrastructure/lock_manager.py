"""
Lock manager for handling concurrent resource access.

Provides:
    - Named locks for different resources
    - Timeout support
    - Deadlock prevention
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import InvoiceError, ErrorCode

logger = get_logger(__name__)


class LockManager:
    """
    Manager for named locks with timeout support.

    Prevents deadlocks and ensures safe concurrent access to resources.
    Uses asyncio.Lock for async-safe operations.
    """

    _instance: LockManager | None = None
    _locks: dict[str, asyncio.Lock] = {}
    _global_lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls) -> LockManager:
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def _get_lock(self, name: str) -> asyncio.Lock:
        """Get or create a named lock."""
        async with self._global_lock:
            if name not in self._locks:
                self._locks[name] = asyncio.Lock()
            return self._locks[name]

    @asynccontextmanager
    async def acquire(
        self,
        resource_name: str,
        timeout: float = 30.0,
    ) -> AsyncIterator[None]:
        """
        Acquire a lock for a named resource with timeout.

        Args:
            resource_name: Name of the resource to lock
            timeout: Maximum time to wait for lock (seconds)

        Yields:
            None when lock is acquired

        Raises:
            InvoiceError: If lock cannot be acquired within timeout

        Example:
            async with lock_manager.acquire("invoice:INV-001"):
                # Critical section
                pass
        """
        lock = await self._get_lock(resource_name)

        try:
            acquired = await asyncio.wait_for(
                lock.acquire(),
                timeout=timeout,
            )
            if not acquired:
                raise InvoiceError(
                    message=f"Failed to acquire lock for {resource_name}",
                    code=ErrorCode.RESOURCE_LOCKED,
                    details={"resource": resource_name},
                )

            logger.debug(f"Lock acquired: {resource_name}")
            yield

        except asyncio.TimeoutError:
            logger.warning(f"Lock timeout: {resource_name}")
            raise InvoiceError(
                message=f"Timeout acquiring lock for {resource_name}",
                code=ErrorCode.TIMEOUT_ERROR,
                details={"resource": resource_name, "timeout": timeout},
            )

        finally:
            if lock.locked():
                lock.release()
                logger.debug(f"Lock released: {resource_name}")

    async def is_locked(self, resource_name: str) -> bool:
        """Check if a resource is currently locked."""
        lock = await self._get_lock(resource_name)
        return lock.locked()

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance and all locks (for testing)."""
        cls._locks.clear()
        cls._instance = None
