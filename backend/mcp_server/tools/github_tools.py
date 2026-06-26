"""MCP tools wrapping the GitHub enterprise connector.

Write operations (create_issue, comment) default to a read-only-safe demo
repo and are intended to be used against a sandbox/test repo, not
production infrastructure.
"""

from backend.config import settings
from backend.mcp_server.connectors.github_client import get_client


def register(mcp):
    @mcp.tool()
    def github_search_issues(query: str, repo: str = "") -> list[dict]:
        """Search issues/PRs in a GitHub repo. Defaults to the configured demo repo."""
        repo = repo or settings.github_default_repo
        return get_client().search_issues(repo, query)

    @mcp.tool()
    def github_search_code(query: str, repo: str = "") -> list[dict]:
        """Search code within a GitHub repo. Defaults to the configured demo repo."""
        repo = repo or settings.github_default_repo
        return get_client().search_code(repo, query)

    @mcp.tool()
    def github_create_issue(title: str, body: str = "", repo: str = "") -> dict:
        """Create a new issue in a GitHub repo. Defaults to the configured demo repo."""
        repo = repo or settings.github_default_repo
        return get_client().create_issue(repo, title, body)

    @mcp.tool()
    def github_comment_on_issue(issue_number: int, body: str, repo: str = "") -> dict:
        """Add a comment to an existing GitHub issue. Defaults to the configured demo repo."""
        repo = repo or settings.github_default_repo
        return get_client().comment_on_issue(repo, issue_number, body)
