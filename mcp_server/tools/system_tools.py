"""Smoke-test tools used to verify MCP plumbing end-to-end."""


def register(mcp):
    @mcp.tool()
    def echo(message: str) -> str:
        """Echo back the given message. Used to verify the MCP round-trip works."""
        return f"echo: {message}"

    @mcp.tool()
    def current_time() -> str:
        """Return the current server time in ISO 8601 format."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
