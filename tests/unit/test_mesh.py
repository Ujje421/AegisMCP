from datetime import UTC, datetime

import pytest

from aegismcp.agent.core import AgentResult
from aegismcp.agent.mesh import agent_as_tool
from aegismcp.kernel.context import create_anonymous_context


class MockAgent:
    async def run(self, query: str, ctx):
        return AgentResult(f"Mocked {query}", 1)

@pytest.mark.asyncio
async def test_agent_as_tool():
    ctx = create_anonymous_context("r1", "t1", "s1", datetime.now(UTC))
    agent = MockAgent()
    
    desc = agent_as_tool("sub_agent", "Does things", agent) # type: ignore
    
    assert desc.name == "sub_agent"
    assert desc.description == "Does things"
    
    res = await desc.fn("hello", ctx)
    assert res == "Mocked hello"
