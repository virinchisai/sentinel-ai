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
                e
                for e in MOCK_EMAILS
                if query_lower in e["subject"].lower()
                or query_lower in e["snippet"].lower()
            ]
            return results[:max_results] if results else MOCK_EMAILS[:max_results]
        from backend.connectors.google import GoogleAPI

        api = GoogleAPI(settings.gmail_credentials_json)
        result = api.request(
            "gmail",
            "GET",
            "messages",
            params={"q": query, "maxResults": max(1, min(max_results, 20))},
        )
        return [
            api.request(
                "gmail",
                "GET",
                "messages/" + message["id"],
                params={"format": "metadata"},
            )
            for message in result.get("messages", [])
        ]

    def get_thread(self, thread_id: str) -> dict:
        if self._use_mock:
            for email in MOCK_EMAILS:
                if email["thread_id"] == thread_id:
                    return {"thread_id": thread_id, "messages": [email]}
            return {"thread_id": thread_id, "messages": []}
        from backend.connectors.google import GoogleAPI
        from urllib.parse import quote

        return GoogleAPI(settings.gmail_credentials_json).request(
            "gmail", "GET", "threads/" + quote(thread_id, safe="")
        )

    def draft_reply(self, thread_id: str, body: str) -> dict:
        if self._use_mock:
            return {
                "status": "draft_created",
                "thread_id": thread_id,
                "body_preview": body[:100],
            }
        from backend.connectors.google import GoogleAPI
        from email.message import EmailMessage
        import base64

        thread = self.get_thread(thread_id)
        messages = thread.get("messages", [])
        if not messages:
            raise ValueError("Thread not found")
        headers = {
            h["name"].lower(): h["value"]
            for h in messages[-1].get("payload", {}).get("headers", [])
        }
        msg = EmailMessage()
        msg["To"] = headers.get("reply-to", headers.get("from", ""))
        msg["Subject"] = "Re: " + headers.get("subject", "")
        if headers.get("message-id"):
            msg["In-Reply-To"] = headers["message-id"]
            msg["References"] = headers["message-id"]
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return GoogleAPI(settings.gmail_credentials_json).request(
            "gmail",
            "POST",
            "drafts",
            json={"message": {"threadId": thread_id, "raw": raw}},
        )


_client: GmailClient | None = None


def get_client() -> GmailClient:
    global _client
    if _client is None:
        _client = GmailClient()
    return _client
