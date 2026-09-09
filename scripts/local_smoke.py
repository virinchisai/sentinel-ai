"""No-cost smoke check for the configured local provider."""

import asyncio
from backend.agents.llm_provider import OllamaProvider, ChatResponse


async def main():
    provider = OllamaProvider()
    parts = []
    async for event in provider.stream(
        [
            {
                "role": "user",
                "content": "Reply with exactly: SentinelAI local inference works.",
            }
        ],
        [],
    ):
        if isinstance(event, ChatResponse):
            print("Final:", event.text)
        else:
            parts.append(event)
    print("Streaming chunks:", len(parts))
    assert parts, "No streaming text received"


asyncio.run(main())
