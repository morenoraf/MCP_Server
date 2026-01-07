"""
Git Synchronization for Multi-Agent Work.

Provides mechanisms for multiple AI agents to work on the same repository
using Git worktrees and branches for isolation.

Features:
    - Git worktree management for agent isolation
    - Branch-based synchronization
    - Conflict detection and resolution
    - Status polling for coordination
"""

from __future__ import annotations

import subprocess
import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum

from invoice_mcp_server.shared.config import Config
from invoice_mcp_server.shared.logging import get_logger
from invoice_mcp_server.shared.exceptions import InvoiceError, ErrorCode

logger = get_logger(__name__)


class AgentStatus(Enum):
    """Status of an agent's work."""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentInfo:
    """Information about an agent's workspace."""
    agent_id: str
    branch_name: str
    worktree_path: str
    status: AgentStatus = AgentStatus.IDLE
    last_sync: datetime | None = None
    current_task: str | None = None


@dataclass
class SyncStatus:
    """Status file for agent coordination."""
    agent_id: str
    status: AgentStatus
    branch: str
    last_commit: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    message: str | None = None


class GitSyncManager:
    """
    Manages Git synchronization for multi-agent work.

    Each agent gets its own worktree and branch to work in isolation.
    Synchronization happens through:
    - Status files (polling)
    - Branch merging
    - Worktree management
    """

    _instance: GitSyncManager | None = None
    _initialized: bool = False

    def __new__(cls) -> GitSyncManager:
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize Git sync manager."""
        if self._initialized:
            return

        self._config = Config()
        self._repo_path: Path | None = None
        self._agents: dict[str, AgentInfo] = {}
        self._sync_dir: Path | None = None
        self._initialized = True

        logger.info("GitSyncManager initialized")

    def set_repo_path(self, path: str | Path) -> None:
        """Set the repository path."""
        self._repo_path = Path(path)
        self._sync_dir = self._repo_path / ".agent_sync"
        self._sync_dir.mkdir(exist_ok=True)
        logger.info(f"Repository path set: {self._repo_path}")

    def _run_git(self, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
        """Run a git command and return (returncode, stdout, stderr)."""
        cmd = ["git"] + list(args)
        cwd = cwd or self._repo_path

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    async def create_agent_workspace(
        self,
        agent_id: str,
        base_branch: str = "main",
    ) -> AgentInfo:
        """
        Create an isolated workspace for an agent.

        Creates a new branch and worktree for the agent to work in.
        """
        if not self._repo_path:
            raise InvoiceError(
                "Repository path not set",
                code=ErrorCode.CONFIGURATION_ERROR,
            )

        branch_name = f"agent/{agent_id}"
        worktree_path = self._repo_path.parent / f"worktree_{agent_id}"

        # Create branch from base
        code, _, err = self._run_git("checkout", "-b", branch_name, base_branch)
        if code != 0 and "already exists" not in err:
            # Branch might already exist, try to check it out
            self._run_git("checkout", branch_name)

        # Go back to base branch in main repo
        self._run_git("checkout", base_branch)

        # Create worktree
        if not worktree_path.exists():
            code, _, err = self._run_git(
                "worktree", "add", str(worktree_path), branch_name
            )
            if code != 0:
                logger.error(f"Failed to create worktree: {err}")
                raise InvoiceError(
                    f"Failed to create worktree: {err}",
                    code=ErrorCode.DATABASE_ERROR,
                )

        agent_info = AgentInfo(
            agent_id=agent_id,
            branch_name=branch_name,
            worktree_path=str(worktree_path),
            status=AgentStatus.IDLE,
        )

        self._agents[agent_id] = agent_info
        await self._write_status(agent_info)

        logger.info(f"Created workspace for agent {agent_id} at {worktree_path}")
        return agent_info

    async def remove_agent_workspace(self, agent_id: str) -> None:
        """Remove an agent's workspace."""
        if agent_id not in self._agents:
            return

        agent_info = self._agents[agent_id]

        # Remove worktree
        self._run_git("worktree", "remove", agent_info.worktree_path, "--force")

        # Optionally delete branch (commented out for safety)
        # self._run_git("branch", "-D", agent_info.branch_name)

        # Remove status file
        if self._sync_dir:
            status_file = self._sync_dir / f"{agent_id}.json"
            if status_file.exists():
                status_file.unlink()

        del self._agents[agent_id]
        logger.info(f"Removed workspace for agent {agent_id}")

    async def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
        task: str | None = None,
        message: str | None = None,
    ) -> None:
        """Update an agent's status."""
        if agent_id not in self._agents:
            raise InvoiceError(
                f"Agent {agent_id} not found",
                code=ErrorCode.NOT_FOUND,
            )

        agent_info = self._agents[agent_id]
        agent_info.status = status
        agent_info.current_task = task
        agent_info.last_sync = datetime.now()

        await self._write_status(agent_info, message)

    async def _write_status(
        self,
        agent_info: AgentInfo,
        message: str | None = None,
    ) -> None:
        """Write agent status to sync file."""
        if not self._sync_dir:
            return

        # Get last commit hash
        code, commit_hash, _ = self._run_git(
            "rev-parse", "HEAD",
            cwd=Path(agent_info.worktree_path) if Path(agent_info.worktree_path).exists() else None,
        )

        status = SyncStatus(
            agent_id=agent_info.agent_id,
            status=agent_info.status,
            branch=agent_info.branch_name,
            last_commit=commit_hash if code == 0 else None,
            message=message,
        )

        status_file = self._sync_dir / f"{agent_info.agent_id}.json"
        status_file.write_text(json.dumps({
            "agent_id": status.agent_id,
            "status": status.status.value,
            "branch": status.branch,
            "last_commit": status.last_commit,
            "timestamp": status.timestamp,
            "message": status.message,
        }, indent=2))

    async def get_all_agent_statuses(self) -> list[dict[str, Any]]:
        """Get status of all agents (polling mechanism)."""
        if not self._sync_dir or not self._sync_dir.exists():
            return []

        statuses = []
        for status_file in self._sync_dir.glob("*.json"):
            try:
                data = json.loads(status_file.read_text())
                statuses.append(data)
            except Exception as e:
                logger.warning(f"Failed to read status file {status_file}: {e}")

        return statuses

    async def sync_from_main(self, agent_id: str) -> bool:
        """Sync agent's branch with main branch."""
        if agent_id not in self._agents:
            return False

        agent_info = self._agents[agent_id]
        worktree = Path(agent_info.worktree_path)

        if not worktree.exists():
            return False

        # Fetch latest
        self._run_git("fetch", "origin", cwd=worktree)

        # Merge main into agent branch
        code, _, err = self._run_git("merge", "origin/main", cwd=worktree)

        if code != 0:
            logger.warning(f"Merge conflict for agent {agent_id}: {err}")
            return False

        logger.info(f"Agent {agent_id} synced with main")
        return True

    async def commit_agent_work(
        self,
        agent_id: str,
        message: str,
    ) -> str | None:
        """Commit agent's work in its worktree."""
        if agent_id not in self._agents:
            return None

        agent_info = self._agents[agent_id]
        worktree = Path(agent_info.worktree_path)

        if not worktree.exists():
            return None

        # Stage all changes
        self._run_git("add", "-A", cwd=worktree)

        # Commit
        code, _, err = self._run_git(
            "commit", "-m", f"[Agent {agent_id}] {message}",
            cwd=worktree,
        )

        if code != 0:
            if "nothing to commit" in err:
                return None
            logger.error(f"Commit failed: {err}")
            return None

        # Get commit hash
        code, commit_hash, _ = self._run_git("rev-parse", "HEAD", cwd=worktree)

        logger.info(f"Agent {agent_id} committed: {commit_hash[:8]}")
        return commit_hash if code == 0 else None

    async def push_agent_work(self, agent_id: str) -> bool:
        """Push agent's branch to remote."""
        if agent_id not in self._agents:
            return False

        agent_info = self._agents[agent_id]
        worktree = Path(agent_info.worktree_path)

        if not worktree.exists():
            return False

        code, _, err = self._run_git(
            "push", "-u", "origin", agent_info.branch_name,
            cwd=worktree,
        )

        if code != 0:
            logger.error(f"Push failed for agent {agent_id}: {err}")
            return False

        logger.info(f"Agent {agent_id} pushed to remote")
        return True

    async def check_conflicts(
        self,
        agent_id: str,
        target_branch: str = "main",
    ) -> list[str]:
        """Check for potential merge conflicts."""
        if agent_id not in self._agents:
            return []

        agent_info = self._agents[agent_id]
        worktree = Path(agent_info.worktree_path)

        if not worktree.exists():
            return []

        # Fetch latest
        self._run_git("fetch", "origin", cwd=worktree)

        # Check for conflicts using merge --no-commit --no-ff
        code, _, err = self._run_git(
            "merge", "--no-commit", "--no-ff", f"origin/{target_branch}",
            cwd=worktree,
        )

        # Abort the merge
        self._run_git("merge", "--abort", cwd=worktree)

        if code != 0 and "CONFLICT" in err:
            # Parse conflict files
            conflicts = []
            for line in err.split("\n"):
                if "CONFLICT" in line:
                    conflicts.append(line)
            return conflicts

        return []

    def list_agents(self) -> list[AgentInfo]:
        """List all registered agents."""
        return list(self._agents.values())

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None
