"""Agent loop: user message -> LLM -> tool calls via MCP -> final response.

Supports optional planning for complex queries, retry with backoff on tool
failures, human-approval gating for destructive actions, and structured tool
call tracing for observability.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from backend.agents import memory
from backend.agents.llm_provider import LLMProvider, get_provider
from backend.agents.mcp_client import MCPToolClient
from backend.agents.planner import (
    DESTRUCTIVE_TOOLS,
    AgentTrace,
    Plan,
    ToolTrace,
    create_plan,
)

MAX_TOOL_ITERATIONS = 10
MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 0.5


@dataclass
class AgentResult:
    text: str
    tool_calls: list[str] = field(default_factory=list)
    trace: AgentTrace = field(default_factory=AgentTrace)
    needs_approval: bool = False
    pending_action: str = ""


class Orchestrator:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        self._provider = provider or get_provider()

    async def chat(self, session_id: str, user_message: str) -> str:
        result = await self.run(session_id, user_message)
        return result.text

    async def run(
        self,
        session_id: str,
        user_message: str,
        enable_planning: bool = True,
        auto_approve: bool = False,
    ) -> AgentResult:
        history = memory.get_history(session_id)
        memory.append(session_id, {"role": "user", "content": user_message})
        history.append({"role": "user", "content": user_message})

        trace = AgentTrace()
        tool_calls_made: list[str] = []

        if enable_planning:
            try:
                plan = create_plan(self._provider, user_message)
                trace.plan = plan
                if plan.requires_approval and not auto_approve:
                    step_descriptions = [
                        f"{'[APPROVAL] ' if s.needs_approval else ''}{s.description}"
                        for s in plan.steps
                    ]
                    return AgentResult(
                        text="I've created a plan that includes actions requiring your approval:\n\n"
                        + "\n".join(f"{i+1}. {d}" for i, d in enumerate(step_descriptions))
                        + "\n\nPlease approve to proceed.",
                        tool_calls=[],
                        trace=trace,
                        needs_approval=True,
                        pending_action=user_message,
                    )
            except Exception:
                pass

        async with MCPToolClient() as mcp_client:
            tools = await mcp_client.list_tool_schemas()

            for _ in range(MAX_TOOL_ITERATIONS):
                response = self._provider.chat(history, tools)
                assistant_msg = self._provider.assistant_message(response)
                history.append(assistant_msg)
                memory.append(session_id, assistant_msg)

                if not response.tool_calls:
                    return AgentResult(
                        text=response.text, tool_calls=tool_calls_made, trace=trace
                    )

                for tool_call in response.tool_calls:
                    if tool_call.name in DESTRUCTIVE_TOOLS and not auto_approve:
                        return AgentResult(
                            text=f"This action requires approval: {tool_call.name}({tool_call.arguments})",
                            tool_calls=tool_calls_made,
                            trace=trace,
                            needs_approval=True,
                            pending_action=f"{tool_call.name}: {tool_call.arguments}",
                        )

                    tool_calls_made.append(tool_call.name)
                    result, tool_trace = await self._call_with_retry(
                        mcp_client, tool_call.name, tool_call.arguments
                    )
                    trace.tool_traces.append(tool_trace)
                    trace.retries += max(0, tool_trace.duration_ms == 0)

                    tool_result_msg = self._provider.tool_result_message(tool_call, result)
                    history.append(tool_result_msg)
                    memory.append(session_id, tool_result_msg)

        return AgentResult(
            text="Reached maximum tool-call iterations without a final answer.",
            tool_calls=tool_calls_made,
            trace=trace,
        )

    async def _call_with_retry(
        self, mcp_client: MCPToolClient, name: str, arguments: dict
    ) -> tuple[str, ToolTrace]:
        last_error = ""
        for attempt in range(MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                result = await mcp_client.call_tool(name, arguments)
                elapsed = (time.monotonic() - start) * 1000
                return result, ToolTrace(
                    tool_name=name,
                    arguments=arguments,
                    result=result[:500],
                    duration_ms=elapsed,
                    success=True,
                )
            except Exception as e:
                last_error = str(e)
                elapsed = (time.monotonic() - start) * 1000
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_BACKOFF_BASE * (2**attempt))

        return f"Error after {MAX_RETRIES + 1} attempts: {last_error}", ToolTrace(
            tool_name=name,
            arguments=arguments,
            result=last_error,
            duration_ms=0,
            success=False,
        )
