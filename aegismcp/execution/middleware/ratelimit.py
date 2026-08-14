import asyncio
import time
from typing import Any

from aegismcp.execution.pipeline import ToolHandler
from aegismcp.kernel.context import AegisContext
from aegismcp.kernel.errors import SecurityError
from aegismcp.tools.descriptor import ToolDescriptor


class RateLimitError(SecurityError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super(SecurityError, self).__init__(message, request_id, is_retryable=True)

class RateLimitMiddleware:
    """A simple token-bucket rate limiter per identity."""
    def __init__(self, tokens_per_minute: int = 60):
        self.tokens_per_minute = float(tokens_per_minute)
        # id -> (tokens, last_refill)
        self.buckets: dict[str, tuple[float, float]] = {}
        self.lock = asyncio.Lock()
        
    async def __call__(
        self, 
        inputs: Any, 
        ctx: AegisContext, 
        descriptor: ToolDescriptor, 
        next_handler: ToolHandler
    ) -> Any:
        caller_id = ctx.caller_identity.id
        now = time.time()
        
        async with self.lock:
            tokens, last_refill = self.buckets.get(caller_id, (self.tokens_per_minute, now))
            
            elapsed = now - last_refill
            refill = elapsed * (self.tokens_per_minute / 60.0)
            tokens = min(self.tokens_per_minute, tokens + refill)
            
            if tokens < 1.0:
                raise RateLimitError("Rate limit exceeded")
                
            tokens -= 1.0
            self.buckets[caller_id] = (tokens, now)
            
        return await next_handler(inputs, ctx, descriptor)
