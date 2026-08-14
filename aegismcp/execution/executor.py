import asyncio
from datetime import UTC, datetime
from typing import Any

from aegismcp.kernel.context import AegisContext
from aegismcp.kernel.errors import ToolTimeoutError
from aegismcp.tools.descriptor import ToolDescriptor


class ToolExecutor:
    async def __call__(self, inputs: Any, ctx: AegisContext, descriptor: ToolDescriptor) -> Any:
        now = datetime.now(UTC)
        if now >= ctx.deadline:
            raise ToolTimeoutError(
                f"Deadline exceeded before starting tool {descriptor.name}", 
                ctx.request_id
            )
            
        remaining_seconds = (ctx.deadline - now).total_seconds()
        
        # Enforce tool-specific timeout if it's tighter than the context deadline
        timeout = min(remaining_seconds, descriptor.timeout_seconds)
        
        try:
            # We assume inputs is a dict for kwargs
            kwargs = inputs if isinstance(inputs, dict) else {}
            
            if asyncio.iscoroutinefunction(descriptor.fn):
                return await asyncio.wait_for(descriptor.fn(**kwargs), timeout=timeout)
            else:
                # Run synchronous function in executor
                loop = asyncio.get_running_loop()
                # Wrap with timeout
                return await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: descriptor.fn(**kwargs)), 
                    timeout=timeout
                )
        except asyncio.TimeoutError:
            raise ToolTimeoutError(
                f"Tool {descriptor.name} timed out after {timeout}s",
                ctx.request_id
            )
