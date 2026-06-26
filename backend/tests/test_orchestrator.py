import pytest

from backend.agents.llm_provider import ChatResponse, LLMProvider, ToolCall
from backend.agents.orchestrator import Orchestrator


class FakeProvider(LLMProvider):
    """Deterministic stand-in for a real LLM: calls `echo` once, then answers."""

    def __init__(self):
        self.call_count = 0

    def chat(self, messages, tools):
        self.call_count += 1
        if self.call_count == 1:
            return ChatResponse(
                text="",
                tool_calls=[ToolCall(id="call-1", name="echo", arguments={"message": "test"})],
                stop_reason="tool_use",
                raw_assistant_message={"role": "assistant", "content": "[calling echo]"},
            )
        return ChatResponse(text="Done: echo: test", tool_calls=[], stop_reason="end")

    def assistant_message(self, response):
        return response.raw_assistant_message or {"role": "assistant", "content": response.text}

    def tool_result_message(self, tool_call, result):
        return {"role": "user", "content": f"tool result for {tool_call.name}: {result}"}


@pytest.mark.asyncio
async def test_orchestrator_executes_tool_call_then_answers():
    orchestrator = Orchestrator(provider=FakeProvider())
    result = await orchestrator.run("test-session-orch", "please echo test", enable_planning=False)
    assert "echo: test" in result.text
    assert "echo" in result.tool_calls
    assert len(result.trace.tool_traces) >= 1
    assert result.trace.tool_traces[0].success
