import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from aegismcp.execution.executor import ToolExecutor
from aegismcp.execution.pipeline import ExecutionPipeline
from aegismcp.kernel.context import create_anonymous_context
from aegismcp.kernel.errors import ToolTimeoutError
from aegismcp.tools.descriptor import ToolDescriptor


@pytest.mark.asyncio
async def test_tool_executor():
    executor = ToolExecutor()
    
    def my_tool(x: int) -> int:
        return x * 2
        
    descriptor = ToolDescriptor(
        name="my_tool", description="", input_schema={}, output_schema=None,
        timeout_seconds=5.0, max_retries=0, retry_delay_seconds=0, is_idempotent=False,
        required_permissions=frozenset(), audit_level="NONE", fn=my_tool
    )
    
    now = datetime.now(UTC)
    ctx = create_anonymous_context("r1", "t1", "s1", now + timedelta(seconds=10))
    
    result = await executor({"x": 5}, ctx, descriptor)
    assert result == 10

@pytest.mark.asyncio
async def test_tool_executor_timeout():
    executor = ToolExecutor()
    
    async def slow_tool():
        await asyncio.sleep(2)
        return "done"
        
    descriptor = ToolDescriptor(
        name="slow_tool", description="", input_schema={}, output_schema=None,
        timeout_seconds=0.1, max_retries=0, retry_delay_seconds=0, is_idempotent=False,
        required_permissions=frozenset(), audit_level="NONE", fn=slow_tool
    )
    
    now = datetime.now(UTC)
    ctx = create_anonymous_context("r1", "t1", "s1", now + timedelta(seconds=10))
    
    with pytest.raises(ToolTimeoutError):
        await executor({}, ctx, descriptor)

@pytest.mark.asyncio
async def test_pipeline():
    async def middleware(inputs, ctx, desc, next_handler):
        inputs["added"] = True
        return await next_handler(inputs, ctx, desc)
        
    executor = ToolExecutor()
    pipeline = ExecutionPipeline([middleware], executor)
    
    def test_tool(added: bool = False):
        return added
        
    descriptor = ToolDescriptor(
        name="test", description="", input_schema={}, output_schema=None,
        timeout_seconds=5.0, max_retries=0, retry_delay_seconds=0, is_idempotent=False,
        required_permissions=frozenset(), audit_level="NONE", fn=test_tool
    )
    
    now = datetime.now(UTC)
    ctx = create_anonymous_context("r1", "t1", "s1", now + timedelta(seconds=10))
    
    result = await pipeline.execute({}, ctx, descriptor)
    assert result is True
