"""Google Calendar connector — uses mock data in demo mode."""

from __future__ import annotations

from backend.config import settings

MOCK_EVENTS = [
    {
        "id": "evt-001",
        "summary": "Team Standup",
        "start": "2025-06-23T09:00:00Z",
        "end": "2025-06-23T09:15:00Z",
        "attendees": ["alice@company.com", "bob@company.com", "you@company.com"],
        "location": "Zoom",
        "recurring": True,
    },
    {
        "id": "evt-002",
        "summary": "Q3 Planning Session",
        "start": "2025-06-24T14:00:00Z",
        "end": "2025-06-24T16:00:00Z",
        "attendees": ["engineering@company.com"],
        "location": "Conference Room A",
        "recurring": False,
    },
    {
        "id": "evt-003",
        "summary": "1:1 with Manager",
        "start": "2025-06-27T10:00:00Z",
        "end": "2025-06-27T10:30:00Z",
        "attendees": ["manager@company.com", "you@company.com"],
        "location": "Zoom",
        "recurring": True,
    },
    {
        "id": "evt-004",
        "summary": "Architecture Review: Auth Service Migration",
        "start": "2025-06-25T11:00:00Z",
        "end": "2025-06-25T12:00:00Z",
        "attendees": ["platform-team@company.com"],
        "location": "Conference Room B",
        "recurring": False,
    },
]


class CalendarClient:
    def __init__(self) -> None:
        self._use_mock = not settings.google_calendar_credentials_json

    def list_events(self, max_results: int = 10) -> list[dict]:
        if self._use_mock:
            return MOCK_EVENTS[:max_results]
        raise NotImplementedError("Real Calendar API not yet configured")

    def create_event(self, summary: str, start: str, end: str, attendees: list[str] | None = None) -> dict:
        if self._use_mock:
            return {
                "status": "created",
                "id": "evt-new-001",
                "summary": summary,
                "start": start,
                "end": end,
                "attendees": attendees or [],
            }
        raise NotImplementedError("Real Calendar API not yet configured")

    def check_availability(self, date: str) -> list[dict]:
        if self._use_mock:
            return [e for e in MOCK_EVENTS if date in e["start"]]
        raise NotImplementedError("Real Calendar API not yet configured")


_client: CalendarClient | None = None


def get_client() -> CalendarClient:
    global _client
    if _client is None:
        _client = CalendarClient()
    return _client
