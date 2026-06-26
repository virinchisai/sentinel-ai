import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_echo_tool_round_trip():
    params = StdioServerParameters(command=sys.executable, args=["-m", "backend.mcp_server.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert "echo" in names
            assert "query_knowledge_base" in names

            result = await session.call_tool("echo", {"message": "ping"})
            text = result.content[0].text
            assert text == "echo: ping"
