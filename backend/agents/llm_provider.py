"""Provider-agnostic LLM interface for tool-calling chat.

Both Anthropic and OpenAI implementations accept/return a common
representation so the orchestrator never branches on provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from backend.config import settings


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ChatResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end"
    raw_assistant_message: Any = None  # provider-native message, fed back for multi-turn tool use


class LLMProviderConfigurationError(RuntimeError):
    """Raised when the selected model provider cannot be used safely."""


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict]) -> ChatResponse:
        """Send messages + available tool schemas, return the model's response."""

    @abstractmethod
    def tool_result_message(self, tool_call: ToolCall, result: Any) -> dict:
        """Build the message dict representing a tool result, in this provider's format."""

    @abstractmethod
    def assistant_message(self, response: ChatResponse) -> dict:
        """Build the message dict representing the assistant turn that produced `response`."""


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        import anthropic

        self._configured = bool(settings.anthropic_api_key)
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    @staticmethod
    def _to_anthropic_tools(tools: list[dict]) -> list[dict]:
        return [
            {
                "name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t.get("input_schema", {"type": "object", "properties": {}}),
            }
            for t in tools
        ]

    def chat(self, messages: list[dict], tools: list[dict]) -> ChatResponse:
        if not self._configured:
            raise LLMProviderConfigurationError("Anthropic API key is not configured")
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=messages,
            tools=self._to_anthropic_tools(tools),
        )
        text_parts = [block.text for block in resp.content if block.type == "text"]
        tool_calls = [
            ToolCall(id=block.id, name=block.name, arguments=block.input)
            for block in resp.content
            if block.type == "tool_use"
        ]
        return ChatResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=resp.stop_reason,
            raw_assistant_message={"role": "assistant", "content": resp.content},
        )

    def assistant_message(self, response: ChatResponse) -> dict:
        return response.raw_assistant_message

    def tool_result_message(self, tool_call: ToolCall, result: Any) -> dict:
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": str(result),
                }
            ],
        }


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        import openai

        self._configured = bool(settings.openai_api_key)
        self._client = openai.OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    @staticmethod
    def _to_openai_tools(tools: list[dict]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
            for t in tools
        ]

    def chat(self, messages: list[dict], tools: list[dict]) -> ChatResponse:
        if not self._configured:
            raise LLMProviderConfigurationError("OpenAI API key is not configured")
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=self._to_openai_tools(tools),
        )
        choice = resp.choices[0]
        msg = choice.message
        tool_calls = [
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=_safe_json(tc.function.arguments),
            )
            for tc in (msg.tool_calls or [])
        ]
        return ChatResponse(
            text=msg.content or "",
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason,
            raw_assistant_message=msg.model_dump(),
        )

    def assistant_message(self, response: ChatResponse) -> dict:
        return response.raw_assistant_message

    def tool_result_message(self, tool_call: ToolCall, result: Any) -> dict:
        return {"role": "tool", "tool_call_id": tool_call.id, "content": str(result)}


def _safe_json(raw: str) -> dict:
    import json

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def get_provider(name: str | None = None) -> LLMProvider:
    name = (name or settings.llm_provider).lower()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unknown LLM provider: {name}")
