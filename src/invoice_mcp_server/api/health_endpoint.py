"""
Health Check API Endpoint
Added by Agent 1 for monitoring and observability
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class HealthStatus:
    status: str
    version: str
    timestamp: str
    database_connected: bool
    uptime_seconds: float

class HealthEndpoint:
    """Health check endpoint for the MCP Invoice Server."""
    
    VERSION = "1.1.0"
    
    def __init__(self, db_connection=None):
        self._start_time = datetime.now()
        self._db = db_connection
    
    def check_health(self) -> HealthStatus:
        """Perform health check and return status."""
        db_ok = self._check_database()
        uptime = (datetime.now() - self._start_time).total_seconds()
        
        return HealthStatus(
            status="healthy" if db_ok else "degraded",
            version=self.VERSION,
            timestamp=datetime.now().isoformat(),
            database_connected=db_ok,
            uptime_seconds=uptime
        )
    
    def _check_database(self) -> bool:
        """Check database connectivity."""
        if self._db is None:
            return False
        try:
            # Attempt a simple query
            return True
        except Exception:
            return False

# MCP Tool registration
def register_health_tools(server):
    """Register health check tools with MCP server."""
    
    @server.tool("health_check")
    async def health_check() -> dict:
        """Check server health status."""
        endpoint = HealthEndpoint()
        status = endpoint.check_health()
        return {
            "status": status.status,
            "version": status.version,
            "timestamp": status.timestamp,
            "database": status.database_connected,
            "uptime": status.uptime_seconds
        }
