"""MCP tools wrapping the Gmail enterprise connector."""

from backend.mcp_server.connectors.gmail_client import get_client


def register(mcp):
    @mcp.tool()
    def gmail_search(query: str, max_results: int = 5) -> list[dict]:
        """Search emails by keyword. Returns matching email threads."""
        return get_client().search(query, max_results)

    @mcp.tool()
    def gmail_get_thread(thread_id: str) -> dict:
        """Read a full email thread by thread ID."""
        return get_client().get_thread(thread_id)

    @mcp.tool()
    def gmail_draft_reply(thread_id: str, body: str) -> dict:
        """Draft a reply to an email thread."""
        return get_client().draft_reply(thread_id, body)
