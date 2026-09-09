"""MCP client session that connects to the local MCP server over stdio
and exposes its tools in a provider-agnostic schema."""

from __future__ import annotations

import sys
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPToolClient:
    def __init__(self, actor=None) -> None:
        self.actor = actor
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def __aenter__(self) -> "MCPToolClient":
        from backend.connectors.credentials import connector_environment

        env = connector_environment(self.actor.user_id) if self.actor else {}
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "backend.mcp_server.server"], env=env
        )
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self._session = await self._stack.enter_async_context(
            ClientSession(read, write)
        )
        await self._session.initialize()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._stack.aclose()

    async def list_tool_schemas(self) -> list[dict]:
        """Return tool schemas in a provider-neutral shape (name/description/input_schema)."""
        assert self._session is not None
        result = await self._session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in result.tools
        ]

    async def call_tool(self, name: str, arguments: dict) -> str:
        assert self._session is not None
        result = await self._session.call_tool(name, arguments)
        if result.isError:
            raise RuntimeError("MCP tool returned an error")
        parts = [block.text for block in result.content if block.type == "text"]
        import json

        for part in parts:
            try:
                value = json.loads(part)
            except (ValueError, TypeError):
                continue
            if isinstance(value, dict) and "error" in value:
                raise RuntimeError("Connector reported an error")
        return "\n".join(parts)
