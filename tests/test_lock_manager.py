"""
Unit tests for lock manager module.

Tests resource locking, timeout handling, and deadlock prevention.
"""

from __future__ import annotations

import asyncio

import pytest

from invoice_mcp_server.infrastructure.lock_manager import LockManager
from invoice_mcp_server.shared.exceptions import InvoiceError


class TestLockManager:
    """Tests for LockManager class."""

    def test_singleton_pattern(self) -> None:
        """Test lock manager singleton pattern."""
        LockManager._instance = None
        manager1 = LockManager()
        manager2 = LockManager()
        assert manager1 is manager2
        LockManager._instance = None

    @pytest.mark.asyncio
    async def test_acquire_lock(self) -> None:
        """Test acquiring a lock."""
        LockManager._instance = None
        LockManager._locks = {}
        manager = LockManager()

        async with manager.acquire("resource-1"):
            assert "resource-1" in manager._locks
            assert manager._locks["resource-1"].locked()

        LockManager._instance = None

    @pytest.mark.asyncio
    async def test_release_lock(self) -> None:
        """Test releasing a lock."""
        LockManager._instance = None
        LockManager._locks = {}
        manager = LockManager()

        async with manager.acquire("resource-2"):
            pass

        assert not manager._locks["resource-2"].locked()
        LockManager._instance = None

    @pytest.mark.asyncio
    async def test_multiple_resources(self) -> None:
        """Test locking multiple resources."""
        LockManager._instance = None
        LockManager._locks = {}
        manager = LockManager()

        async with manager.acquire("resource-a"):
            async with manager.acquire("resource-b"):
                assert manager._locks["resource-a"].locked()
                assert manager._locks["resource-b"].locked()

        LockManager._instance = None

    @pytest.mark.asyncio
    async def test_lock_timeout(self) -> None:
        """Test lock timeout raises InvoiceError."""
        LockManager._instance = None
        LockManager._locks = {}
        manager = LockManager()

        async with manager.acquire("timeout-resource"):
            # Try to acquire same lock with short timeout
            with pytest.raises(InvoiceError) as exc_info:
                async with manager.acquire("timeout-resource", timeout=0.1):
                    pass
            assert "Timeout" in str(exc_info.value)

        LockManager._instance = None

    @pytest.mark.asyncio
    async def test_concurrent_access(self) -> None:
        """Test concurrent access to same resource."""
        LockManager._instance = None
        LockManager._locks = {}
        manager = LockManager()
        results = []

        async def worker(id: int) -> None:
            async with manager.acquire("shared-resource"):
                results.append(f"start-{id}")
                await asyncio.sleep(0.1)
                results.append(f"end-{id}")

        await asyncio.gather(
            worker(1),
            worker(2),
        )

        # Verify sequential execution (no interleaving)
        assert results[0] == "start-1" or results[0] == "start-2"
        assert results[1].startswith("end")

        LockManager._instance = None

    @pytest.mark.asyncio
    async def test_is_locked(self) -> None:
        """Test checking if resource is locked."""
        LockManager._instance = None
        LockManager._locks = {}
        manager = LockManager()

        assert not await manager.is_locked("check-resource")

        async with manager.acquire("check-resource"):
            assert await manager.is_locked("check-resource")

        assert not await manager.is_locked("check-resource")

        LockManager._instance = None

    @pytest.mark.asyncio
    async def test_exception_releases_lock(self) -> None:
        """Test that exceptions release the lock."""
        LockManager._instance = None
        LockManager._locks = {}
        manager = LockManager()

        try:
            async with manager.acquire("exception-resource"):
                raise ValueError("Test error")
        except ValueError:
            pass

        assert not await manager.is_locked("exception-resource")

        LockManager._instance = None
