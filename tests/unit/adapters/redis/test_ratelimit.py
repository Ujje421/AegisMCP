import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import pytest
import redis.asyncio as redis
from redis.exceptions import NoScriptError

from aegismcp.adapters.redis.ratelimit import RateLimitError, RedisRateLimiter
from aegismcp.kernel.context import AegisContext, Identity
from aegismcp.tools.descriptor import ToolDescriptor


# Mock Redis Client
class MockAsyncRedis:
    def __init__(self):
        self.data = {}
        self.scripts = {}

    async def script_load(self, script: str) -> str:
        sha = "mock_sha"
        self.scripts[sha] = script
        return sha

    async def evalsha(self, sha: str, numkeys: int, *keys_and_args: Any) -> Any:
        if sha not in self.scripts:
            raise NoScriptError("Script not found")

        # Basic emulation of the lua script
        bucket_key = keys_and_args[0]
        rate = float(keys_and_args[1])
        now = float(keys_and_args[2])

        state = self.data.get(bucket_key)
        if state is None:
            tokens = rate
            last_refill = now
        else:
            tokens = float(state["tokens"])
            last_refill = float(state["last_refill"])
            elapsed = now - last_refill
            refill = elapsed * (rate / 60.0)
            tokens = min(rate, tokens + refill)

        if tokens < 1.0:
            self.data[bucket_key] = {"tokens": tokens, "last_refill": now}
            return -1

        tokens -= 1.0
        self.data[bucket_key] = {"tokens": tokens, "last_refill": now}
        return tokens


async def mock_next_handler(inputs: Any, ctx: AegisContext, descriptor: ToolDescriptor) -> str:
    return "success"


@pytest.fixture
def mock_redis():
    return MockAsyncRedis()


@pytest.fixture
def context():
    return AegisContext(
        request_id="req-123",
        trace_id="trace-123",
        span_id="span-123",
        caller_identity=Identity(id="user_1", type="user"),
        permissions=frozenset(),
        deadline=datetime.now(timezone.utc),
        metadata={},
        baggage={}
    )


@pytest.fixture
def descriptor():
    return ToolDescriptor(
        name="test_tool",
        description="test",
        input_schema={},
        output_schema={},
        timeout_seconds=5.0,
        max_retries=0,
        retry_delay_seconds=0.0,
        is_idempotent=True,
        required_permissions=frozenset(),
        audit_level="none",
        fn=lambda: None
    )


@pytest.mark.asyncio
async def test_redis_ratelimiter_allows_request(mock_redis, context, descriptor):
    limiter = RedisRateLimiter(redis_client=mock_redis, tokens_per_minute=5)
    
    # Should allow 5 requests
    for _ in range(5):
        result = await limiter({}, context, descriptor, mock_next_handler)
        assert result == "success"

    # 6th request should fail immediately (no sleep)
    with pytest.raises(RateLimitError):
        await limiter({}, context, descriptor, mock_next_handler)


@pytest.mark.asyncio
async def test_redis_ratelimiter_script_reload(mock_redis, context, descriptor):
    limiter = RedisRateLimiter(redis_client=mock_redis, tokens_per_minute=5)
    
    result = await limiter({}, context, descriptor, mock_next_handler)
    assert result == "success"
    
    # Simulate Redis being flushed (script disappears)
    mock_redis.scripts.clear()
    
    # The limiter should automatically catch NoScriptError, reload it, and succeed
    result2 = await limiter({}, context, descriptor, mock_next_handler)
    assert result2 == "success"
