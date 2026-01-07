"""
Multi-Agent Synchronization Tools.

MCP tools for managing multi-agent work with Git worktrees.
Enables multiple AI agents to work on the same repository safely.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from invoice_mcp_server.mcp.primitives import Tool
from invoice_mcp_server.mcp.protocol import ToolResult
from invoice_mcp_server.infrastructure.git_sync import GitSyncManager, AgentStatus
from invoice_mcp_server.shared.logging import get_logger

if TYPE_CHECKING:
    from invoice_mcp_server.mcp.server import InvoiceMCPServer

logger = get_logger(__name__)


class CreateAgentWorkspaceTool(Tool):
    """Tool to create an isolated workspace for an agent."""

    name = "create_agent_workspace"
    description = "Create an isolated Git worktree for an agent to work in"

    def __init__(self, server: InvoiceMCPServer) -> None:
        super().__init__(server)
        self._sync_manager = GitSyncManager()

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Unique identifier for the agent",
                },
                "repo_path": {
                    "type": "string",
                    "description": "Path to the Git repository",
                },
                "base_branch": {
                    "type": "string",
                    "description": "Base branch to create from",
                    "default": "main",
                },
            },
            "required": ["agent_id", "repo_path"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        agent_id: str = kwargs.get("agent_id", "")
        repo_path: str = kwargs.get("repo_path", "")
        base_branch: str = kwargs.get("base_branch", "main")

        if not agent_id or not repo_path:
            return self._error_result("agent_id and repo_path are required")

        try:
            self._sync_manager.set_repo_path(repo_path)
            agent_info = await self._sync_manager.create_agent_workspace(
                agent_id=agent_id,
                base_branch=base_branch,
            )

            return self._success_result(
                f"Created workspace for agent '{agent_id}'\n"
                f"Branch: {agent_info.branch_name}\n"
                f"Worktree: {agent_info.worktree_path}"
            )
        except Exception as e:
            logger.error(f"Failed to create workspace: {e}")
            return self._error_result(str(e))


class UpdateAgentStatusTool(Tool):
    """Tool to update an agent's status for coordination."""

    name = "update_agent_status"
    description = "Update the status of an agent for coordination with other agents"

    def __init__(self, server: InvoiceMCPServer) -> None:
        super().__init__(server)
        self._sync_manager = GitSyncManager()

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier",
                },
                "status": {
                    "type": "string",
                    "enum": ["idle", "working", "waiting", "completed", "error"],
                    "description": "Current agent status",
                },
                "task": {
                    "type": "string",
                    "description": "Current task description",
                },
                "message": {
                    "type": "string",
                    "description": "Status message for other agents",
                },
            },
            "required": ["agent_id", "status"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        agent_id: str = kwargs.get("agent_id", "")
        status_str: str = kwargs.get("status", "")
        task: str | None = kwargs.get("task")
        message: str | None = kwargs.get("message")

        if not agent_id or not status_str:
            return self._error_result("agent_id and status are required")

        try:
            status = AgentStatus(status_str)
            await self._sync_manager.update_agent_status(
                agent_id=agent_id,
                status=status,
                task=task,
                message=message,
            )

            return self._success_result(
                f"Agent '{agent_id}' status updated to '{status_str}'"
            )
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return self._error_result(str(e))


class CommitAgentWorkTool(Tool):
    """Tool to commit agent's work in its worktree."""

    name = "commit_agent_work"
    description = "Commit the agent's work in its isolated worktree"

    def __init__(self, server: InvoiceMCPServer) -> None:
        super().__init__(server)
        self._sync_manager = GitSyncManager()

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier",
                },
                "message": {
                    "type": "string",
                    "description": "Commit message",
                },
            },
            "required": ["agent_id", "message"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        agent_id: str = kwargs.get("agent_id", "")
        message: str = kwargs.get("message", "")

        if not agent_id or not message:
            return self._error_result("agent_id and message are required")

        try:
            commit_hash = await self._sync_manager.commit_agent_work(
                agent_id=agent_id,
                message=message,
            )

            if commit_hash:
                return self._success_result(
                    f"Committed: {commit_hash[:8]} - {message}"
                )
            else:
                return self._success_result("Nothing to commit")
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            return self._error_result(str(e))


class SyncFromMainTool(Tool):
    """Tool to sync agent's branch with main."""

    name = "sync_from_main"
    description = "Sync agent's branch with the main branch"

    def __init__(self, server: InvoiceMCPServer) -> None:
        super().__init__(server)
        self._sync_manager = GitSyncManager()

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier",
                },
            },
            "required": ["agent_id"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        agent_id: str = kwargs.get("agent_id", "")

        if not agent_id:
            return self._error_result("agent_id is required")

        try:
            success = await self._sync_manager.sync_from_main(agent_id)

            if success:
                return self._success_result(
                    f"Agent '{agent_id}' synced with main branch"
                )
            else:
                return self._error_result("Sync failed - possible merge conflict")
        except Exception as e:
            logger.error(f"Failed to sync: {e}")
            return self._error_result(str(e))


class CheckConflictsTool(Tool):
    """Tool to check for merge conflicts before merging."""

    name = "check_conflicts"
    description = "Check for potential merge conflicts with main branch"

    def __init__(self, server: InvoiceMCPServer) -> None:
        super().__init__(server)
        self._sync_manager = GitSyncManager()

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier",
                },
            },
            "required": ["agent_id"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        agent_id: str = kwargs.get("agent_id", "")

        if not agent_id:
            return self._error_result("agent_id is required")

        try:
            conflicts = await self._sync_manager.check_conflicts(agent_id)

            if conflicts:
                return self._success_result(
                    "Conflicts detected:\n" + "\n".join(conflicts)
                )
            else:
                return self._success_result("No conflicts detected - safe to merge")
        except Exception as e:
            logger.error(f"Failed to check conflicts: {e}")
            return self._error_result(str(e))


def get_sync_tools() -> list[type[Tool]]:
    """Get all sync tools."""
    return [
        CreateAgentWorkspaceTool,
        UpdateAgentStatusTool,
        CommitAgentWorkTool,
        SyncFromMainTool,
        CheckConflictsTool,
    ]
