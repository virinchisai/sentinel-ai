"""Gmail connector — uses mock data in demo mode, real Gmail API when credentials are configured."""

from __future__ import annotations

from backend.config import settings

MOCK_EMAILS = [
    {
        "id": "msg-001",
        "thread_id": "thread-001",
        "from": "engineering@company.com",
        "to": "team@company.com",
        "subject": "Q3 Planning Kickoff",
        "snippet": "Hi team, let's schedule our Q3 planning session. I'm thinking next Tuesday at 2pm...",
        "date": "2025-06-20T10:30:00Z",
        "labels": ["INBOX", "IMPORTANT"],
    },
    {
        "id": "msg-002",
        "thread_id": "thread-002",
        "from": "hr@company.com",
        "to": "all-employees@company.com",
        "subject": "Updated PTO Policy - Effective July 1st",
        "snippet": "Please review the updated PTO policy attached. Key change: carryover limit increased to 10 days...",
        "date": "2025-06-19T14:00:00Z",
        "labels": ["INBOX"],
    },
    {
        "id": "msg-003",
        "thread_id": "thread-003",
        "from": "oncall@company.com",
        "to": "sre-team@company.com",
        "subject": "SEV2 Incident: API Latency Spike",
        "snippet": "API p99 latency exceeded 2s threshold at 03:45 UTC. Root cause identified as connection pool exhaustion...",
        "date": "2025-06-18T03:45:00Z",
        "labels": ["INBOX", "URGENT"],
    },
    {
        "id": "msg-004",
        "thread_id": "thread-004",
        "from": "manager@company.com",
        "to": "you@company.com",
        "subject": "1:1 Agenda for Friday",
        "snippet": "Topics for our 1:1: project status update, career growth discussion, feedback on the new deployment process...",
        "date": "2025-06-17T09:00:00Z",
        "labels": ["INBOX"],
    },
]


class GmailClient:
    def __init__(self) -> None:
        self._use_mock = not settings.gmail_credentials_json

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        if self._use_mock:
            query_lower = query.lower()
            results = [
                e for e in MOCK_EMAILS
                if query_lower in e["subject"].lower() or query_lower in e["snippet"].lower()
            ]
            return results[:max_results] if results else MOCK_EMAILS[:max_results]
        raise NotImplementedError("Real Gmail API not yet configured")

    def get_thread(self, thread_id: str) -> dict:
        if self._use_mock:
            for email in MOCK_EMAILS:
                if email["thread_id"] == thread_id:
                    return {"thread_id": thread_id, "messages": [email]}
            return {"thread_id": thread_id, "messages": []}
        raise NotImplementedError("Real Gmail API not yet configured")

    def draft_reply(self, thread_id: str, body: str) -> dict:
        if self._use_mock:
            return {"status": "draft_created", "thread_id": thread_id, "body_preview": body[:100]}
        raise NotImplementedError("Real Gmail API not yet configured")


_client: GmailClient | None = None


def get_client() -> GmailClient:
    global _client
    if _client is None:
        _client = GmailClient()
    return _client
