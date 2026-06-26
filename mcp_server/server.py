"""MCP server entrypoint.

Run directly for stdio transport (used by the agent's MCP client):
    python -m mcp_server.server

Or run with streamable-http transport (used for Docker/cloud deployment):
    python -m mcp_server.server --http
"""

import sys

from mcp.server.fastmcp import FastMCP

from mcp_server.tools import github_tools, rag_tools, system_tools

mcp = FastMCP("enterprise-ai-assistant")

system_tools.register(mcp)
github_tools.register(mcp)
rag_tools.register(mcp)


def _run_http() -> None:
    import uvicorn

    from mcp_server.auth import BearerAuthMiddleware

    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)

    @app.route("/health")
    async def health(request):
        from starlette.responses import JSONResponse

        return JSONResponse({"status": "ok"})

    uvicorn.run(app, host=mcp.settings.host, port=mcp.settings.port)


def main() -> None:
    if "--http" in sys.argv:
        _run_http()
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
