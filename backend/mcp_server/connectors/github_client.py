"""Thin wrapper around the GitHub REST API."""

import httpx

from backend.config import settings

BASE_URL = "https://api.github.com"


def _headers() -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


class GitHubClient:
    def __init__(self) -> None:
        self._client = httpx.Client(base_url=BASE_URL, headers=_headers(), timeout=15.0)

    def search_issues(self, repo: str, query: str, limit: int = 5) -> list[dict]:
        q = f"repo:{repo} {query}"
        resp = self._client.get("/search/issues", params={"q": q, "per_page": limit})
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [
            {
                "number": item["number"],
                "title": item["title"],
                "state": item["state"],
                "url": item["html_url"],
                "body": (item.get("body") or "")[:300],
            }
            for item in items
        ]

    def search_code(self, repo: str, query: str, limit: int = 5) -> list[dict]:
        q = f"repo:{repo} {query}"
        resp = self._client.get("/search/code", params={"q": q, "per_page": limit})
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [
            {"name": item["name"], "path": item["path"], "url": item["html_url"]}
            for item in items
        ]

    def create_issue(self, repo: str, title: str, body: str = "") -> dict:
        resp = self._client.post(f"/repos/{repo}/issues", json={"title": title, "body": body})
        resp.raise_for_status()
        data = resp.json()
        return {"number": data["number"], "url": data["html_url"]}

    def comment_on_issue(self, repo: str, issue_number: int, body: str) -> dict:
        resp = self._client.post(
            f"/repos/{repo}/issues/{issue_number}/comments", json={"body": body}
        )
        resp.raise_for_status()
        data = resp.json()
        return {"id": data["id"], "url": data["html_url"]}


_client: GitHubClient | None = None


def get_client() -> GitHubClient:
    global _client
    if _client is None:
        _client = GitHubClient()
    return _client
