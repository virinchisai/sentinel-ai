"""MCP tools for sandboxed file system access."""

from backend.mcp_server.connectors.filesystem_client import get_client


def register(mcp):
    @mcp.tool()
    def fs_list_files(directory: str = ".") -> list[dict]:
        """List files in a workspace directory."""
        return get_client().list_files(directory)

    @mcp.tool()
    def fs_read_file(path: str) -> dict:
        """Read the contents of a file from the workspace."""
        return get_client().read_file(path)

    @mcp.tool()
    def fs_search(query: str, directory: str = ".") -> list[dict]:
        """Search for a text string across files in the workspace."""
        return get_client().search_files(query, directory)
