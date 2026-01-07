"""
Multi-Agent Synchronization Resources.

MCP resources for monitoring agent coordination status.
Provides polling-based visibility into all agent activities.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from invoice_mcp_server.mcp.primitives import DynamicResource
from invoice_mcp_server.mcp.protocol import ResourceDefinition
from invoice_mcp_server.infrastructure.git_sync import GitSyncManager
from invoice_mcp_server.shared.logging import get_logger

if TYPE_CHECKING:
    from invoice_mcp_server.mcp.server import InvoiceMCPServer

logger = get_logger(__name__)


class AgentStatusesResource(DynamicResource):
    """Resource showing all agent statuses for coordination."""

    uri = "invoice://agents/status"
    name = "Agent Statuses"
    description = "Current status of all agents for coordination (polling)"

    def __init__(self, server: InvoiceMCPServer) -> None:
        super().__init__(server)
        self._sync_manager = GitSyncManager()

    def get_definition(self) -> ResourceDefinition:
        return ResourceDefinition(
            uri=self.uri,
            name=self.name,
            description=self.description,
            mimeType=self.mime_type,
        )

    async def read(self) -> dict[str, Any]:
        """Read all agent statuses."""
        statuses = await self._sync_manager.get_all_agent_statuses()

        # Also include registered agents
        agents = self._sync_manager.list_agents()
        registered = [
            {
                "agent_id": a.agent_id,
                "branch": a.branch_name,
                "worktree": a.worktree_path,
                "status": a.status.value,
                "current_task": a.current_task,
            }
            for a in agents
        ]

        return {
            "registered_agents": registered,
            "status_files": statuses,
            "total_agents": len(registered),
        }


class AgentWorkspacesResource(DynamicResource):
    """Resource showing all agent workspaces."""

    uri = "invoice://agents/workspaces"
    name = "Agent Workspaces"
    description = "Git worktrees and branches for each agent"

    def __init__(self, server: InvoiceMCPServer) -> None:
        super().__init__(server)
        self._sync_manager = GitSyncManager()

    def get_definition(self) -> ResourceDefinition:
        return ResourceDefinition(
            uri=self.uri,
            name=self.name,
            description=self.description,
            mimeType=self.mime_type,
        )

    async def read(self) -> dict[str, Any]:
        """Read all agent workspaces."""
        agents = self._sync_manager.list_agents()

        workspaces = []
        for agent in agents:
            workspaces.append({
                "agent_id": agent.agent_id,
                "branch": agent.branch_name,
                "worktree_path": agent.worktree_path,
                "status": agent.status.value,
                "last_sync": agent.last_sync.isoformat() if agent.last_sync else None,
            })

        return {
            "workspaces": workspaces,
            "total": len(workspaces),
        }


def get_sync_resources() -> list[type[DynamicResource]]:
    """Get all sync resources."""
    return [
        AgentStatusesResource,
        AgentWorkspacesResource,
    ]
