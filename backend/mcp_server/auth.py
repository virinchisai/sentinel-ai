"""Bearer-token auth for the MCP server's HTTP transport.

The MCP server is mounted behind a Starlette app; this middleware checks
the Authorization header on every request against the configured token
before MCP traffic is allowed through.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.config import settings


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health",):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        expected = f"Bearer {settings.mcp_auth_token}"
        if auth_header != expected:
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        return await call_next(request)
