import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from aegismcp.agent.core import AegisAgent
from aegismcp.agent.models import (
    GenerationConfig,
    Message,
    ModelProvider,
    ModelResponse,
    ModelResponseChunk,
    ToolCall,
)
from aegismcp.client.core import AegisClient
from aegismcp.kernel.context import AegisContext, create_anonymous_context
from aegismcp.tools.descriptor import ToolDescriptor
from aegismcp.transports.base import Transport


class DummyModelProvider(ModelProvider):
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDescriptor],
        config: GenerationConfig,
        ctx: AegisContext,
    ) -> ModelResponse:
        # Dummy logic: if asked for weather, call get_weather tool.
        # If tool results provided, return final answer.
        if any(m.role == "tool" for m in messages):
            return ModelResponse("It is sunny today!", [])
        return ModelResponse(
            "Checking weather...", [ToolCall("call_1", "get_weather", {"location": "Seattle"})]
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDescriptor],
        config: GenerationConfig,
        ctx: AegisContext,
    ) -> AsyncIterator[ModelResponseChunk]:
        yield ModelResponseChunk("")


class MockTransport(Transport):
    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def send(self, data: bytes) -> None:
        pass

    async def receive(self) -> bytes:
        return b""


async def main() -> None:
    ctx = create_anonymous_context("r1", "t1", "s1", datetime.now(UTC))

    # 1. Define tools (Usually loaded from a remote AegisMCP server via client)
    desc = ToolDescriptor(
        name="get_weather",
        description="Get weather",
        input_schema={},
        output_schema=None,
        timeout_seconds=5.0,
        max_retries=0,
        retry_delay_seconds=0,
        is_idempotent=True,
        required_permissions=frozenset(),
        audit_level="NONE",
        fn=lambda: 1,
    )
    registry = {"get_weather": desc}

    # 2. Setup Dummy Client (In real life, connect to WebSocketTransport)
    client = AegisClient(MockTransport())

    async def mock_request(*args, **kwargs):
        return {"content": "Sunny"}

    client.request = mock_request  # type: ignore

    # 3. Setup Agent
    agent = AegisAgent(model=DummyModelProvider(), client=client, tool_registry=registry)

    print("User: What is the weather in Seattle?")
    result = await agent.run("What is the weather in Seattle?", ctx)

    print(f"Agent ({result.turns} turns): {result.content}")


if __name__ == "__main__":
    asyncio.run(main())
