from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest

from aegismcp.agent.core import AegisAgent, AgentError
from aegismcp.agent.models import (
    GenerationConfig,
    Message,
    ModelProvider,
    ModelResponse,
    ModelResponseChunk,
    ToolCall,
)
from aegismcp.client.core import AegisClient
from aegismcp.client.pool import ConnectionPool
from aegismcp.kernel.context import AegisContext, create_anonymous_context
from aegismcp.tools.descriptor import ToolDescriptor


class MockModelProvider(ModelProvider):
    def __init__(self, responses: list[ModelResponse]):
        self.responses = responses
        self.call_count = 0

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDescriptor],
        config: GenerationConfig,
        ctx: AegisContext,
    ) -> ModelResponse:
        resp = self.responses[self.call_count]
        self.call_count += 1
        return resp

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDescriptor],
        config: GenerationConfig,
        ctx: AegisContext,
    ) -> AsyncIterator[ModelResponseChunk]:
        yield ModelResponseChunk("")


@pytest.mark.asyncio
async def test_agent_loop_success():
    ctx = create_anonymous_context("r1", "t1", "s1", datetime.now(UTC))

    desc1 = ToolDescriptor(
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
    registry = {"get_weather": desc1}

    provider = MockModelProvider(
        [
            ModelResponse("Let me check", [ToolCall("call1", "get_weather", {"location": "NYC"})]),
            ModelResponse("It is sunny", []),
        ]
    )

    client = AegisClient(None)  # type: ignore

    async def mock_call_tool(*args: Any, **kwargs: Any) -> dict[str, str]:
        return {"content": "sunny"}

    client.call_tool = mock_call_tool  # type: ignore

    agent = AegisAgent(model=provider, client=client, tool_registry=registry)

    res = await agent.run("What is the weather?", ctx)
    assert res.content == "It is sunny"
    assert res.turns == 2
    assert provider.call_count == 2


@pytest.mark.asyncio
async def test_agent_max_turns():
    ctx = create_anonymous_context("r1", "t1", "s1", datetime.now(UTC))

    provider = MockModelProvider(
        [ModelResponse("looping", [ToolCall("call1", "get_weather", {})]) for _ in range(10)]
    )

    client = AegisClient(None)  # type: ignore

    async def mock_call_tool(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}

    client.call_tool = mock_call_tool  # type: ignore

    agent = AegisAgent(model=provider, client=client, tool_registry={}, max_turns=3)

    with pytest.raises(AgentError) as exc:
        await agent.run("hello", ctx)

    assert "Max turns exceeded" in str(exc.value)
    assert provider.call_count == 3
