"""MCP tools for read-only database queries and schema introspection."""

from backend.mcp_server.connectors.database_client import get_client


def register(mcp):
    @mcp.tool()
    def db_query(sql: str) -> dict:
        """Execute a read-only SQL query against the enterprise database. Only SELECT statements are allowed."""
        return get_client().execute_query(sql)

    @mcp.tool()
    def db_describe_schema() -> list[dict]:
        """List all tables and their columns in the enterprise database."""
        return get_client().describe_schema()
