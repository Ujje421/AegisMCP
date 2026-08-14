import asyncio
from typing import AsyncIterator
from aegismcp.kernel.context import create_anonymous_context
from aegismcp.client.core import AegisClient
from aegismcp.client.pool import ConnectionPool
from aegismcp.agent.core import AegisAgent
from aegismcp.agent.models import ModelProvider, ModelResponse, ToolCall, Message, GenerationConfig, ModelResponseChunk
from aegismcp.tools.descriptor import ToolDescriptor
from datetime import datetime, UTC

class DummyModelProvider(ModelProvider):
    async def generate(self, messages, tools, config, ctx) -> ModelResponse:
        # Dummy logic: if asked for weather, call get_weather tool. 
        # If tool results provided, return final answer.
        if any(m.role == "tool" for m in messages):
            return ModelResponse("It is sunny today!", [])
        return ModelResponse(
            "Checking weather...", 
            [ToolCall("call_1", "get_weather", {"location": "Seattle"})]
        )
    
    async def stream(self, messages, tools, config, ctx) -> AsyncIterator[ModelResponseChunk]:
        yield ModelResponseChunk("")

async def main() -> None:
    ctx = create_anonymous_context("r1", "t1", "s1", datetime.now(UTC))
    
    # 1. Define tools (Usually loaded from a remote AegisMCP server via client)
    desc = ToolDescriptor(
        name="get_weather", description="Get weather", input_schema={},
        output_schema=None, timeout_seconds=5.0, max_retries=0, retry_delay_seconds=0,
        is_idempotent=True, required_permissions=frozenset(), audit_level="NONE", fn=lambda: 1
    )
    registry = {"get_weather": desc}
    
    # 2. Setup Dummy Client (In real life, connect to WebSocketTransport)
    client = AegisClient(ConnectionPool())
    async def mock_request(*args, **kwargs):
        return {"content": "Sunny"}
    client.request = mock_request # type: ignore
    
    # 3. Setup Agent
    agent = AegisAgent(model=DummyModelProvider(), client=client, tool_registry=registry)
    
    print("User: What is the weather in Seattle?")
    result = await agent.run("What is the weather in Seattle?", ctx)
    
    print(f"Agent ({result.turns} turns): {result.content}")

if __name__ == "__main__":
    asyncio.run(main())
