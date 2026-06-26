"""Agent loop: user message -> LLM -> tool calls via MCP -> final response."""

from __future__ import annotations

from dataclasses import dataclass, field

from agent import memory
from agent.llm_provider import LLMProvider, get_provider
from agent.mcp_client import MCPToolClient

MAX_TOOL_ITERATIONS = 6


@dataclass
class AgentResult:
    text: str
    tool_calls: list[str] = field(default_factory=list)  # tool names invoked, in order


class Orchestrator:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        self._provider = provider or get_provider()

    async def chat(self, session_id: str, user_message: str) -> str:
        result = await self.run(session_id, user_message)
        return result.text

    async def run(self, session_id: str, user_message: str) -> AgentResult:
        history = memory.get_history(session_id)
        history.append({"role": "user", "content": user_message})
        tool_calls_made: list[str] = []

        async with MCPToolClient() as mcp_client:
            tools = await mcp_client.list_tool_schemas()

            for _ in range(MAX_TOOL_ITERATIONS):
                response = self._provider.chat(history, tools)
                history.append(self._provider.assistant_message(response))

                if not response.tool_calls:
                    return AgentResult(text=response.text, tool_calls=tool_calls_made)

                for tool_call in response.tool_calls:
                    tool_calls_made.append(tool_call.name)
                    result = await mcp_client.call_tool(tool_call.name, tool_call.arguments)
                    history.append(self._provider.tool_result_message(tool_call, result))

        return AgentResult(
            text="Reached maximum tool-call iterations without a final answer.",
            tool_calls=tool_calls_made,
        )
