"""MCP tools wrapping the Calendar enterprise connector."""

from backend.mcp_server.connectors.calendar_client import get_client


def register(mcp):
    @mcp.tool()
    def calendar_list_events(max_results: int = 10) -> list[dict]:
        """List upcoming calendar events."""
        return get_client().list_events(max_results)

    @mcp.tool()
    def calendar_create_event(summary: str, start: str, end: str, attendees: str = "") -> dict:
        """Create a new calendar event. Attendees as comma-separated emails."""
        attendee_list = [a.strip() for a in attendees.split(",") if a.strip()] if attendees else []
        return get_client().create_event(summary, start, end, attendee_list)

    @mcp.tool()
    def calendar_check_availability(date: str) -> list[dict]:
        """Check what events exist on a given date (YYYY-MM-DD format)."""
        return get_client().check_availability(date)
