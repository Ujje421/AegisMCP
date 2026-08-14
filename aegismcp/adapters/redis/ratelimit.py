import time
from typing import Any

import redis.asyncio as redis
from redis.exceptions import NoScriptError

from aegismcp.execution.pipeline import ToolHandler
from aegismcp.kernel.context import AegisContext
from aegismcp.kernel.errors import SecurityError
from aegismcp.tools.descriptor import ToolDescriptor


class RateLimitError(SecurityError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super(SecurityError, self).__init__(message, request_id, is_retryable=True)


class RedisRateLimiter:
    """
    A distributed token-bucket rate limiter backed by Redis.
    Uses an atomic Lua script to evaluate and deduct tokens.
    """

    # Lua script for token bucket algorithm
    # KEYS[1] - bucket key
    # ARGV[1] - tokens per minute
    # ARGV[2] - current time in seconds
    LUA_SCRIPT = """
    local bucket_key = KEYS[1]
    local rate = tonumber(ARGV[1])
    local now = tonumber(ARGV[2])

    local state = redis.call("HMGET", bucket_key, "tokens", "last_refill")
    local tokens = tonumber(state[1])
    local last_refill = tonumber(state[2])

    if tokens == nil then
        tokens = rate
        last_refill = now
    else
        local elapsed = now - last_refill
        local refill = elapsed * (rate / 60.0)
        tokens = math.min(rate, tokens + refill)
    end

    if tokens < 1.0 then
        -- We update the state anyway so the TTL is refreshed
        redis.call("HMSET", bucket_key, "tokens", tokens, "last_refill", now)
        redis.call("EXPIRE", bucket_key, 120)
        return -1
    end

    tokens = tokens - 1.0
    redis.call("HMSET", bucket_key, "tokens", tokens, "last_refill", now)
    redis.call("EXPIRE", bucket_key, 120)

    return tokens
    """

    def __init__(
        self, redis_client: redis.Redis, tokens_per_minute: int = 60, key_prefix: str = "ratelimit"
    ):
        self.redis = redis_client
        self.tokens_per_minute = float(tokens_per_minute)
        self.key_prefix = key_prefix
        self._script_sha = None

    async def _load_script(self) -> str:
        if self._script_sha is None:
            self._script_sha = await self.redis.script_load(self.LUA_SCRIPT)
        assert self._script_sha is not None
        return self._script_sha

    async def __call__(
        self, inputs: Any, ctx: AegisContext, descriptor: ToolDescriptor, next_handler: ToolHandler
    ) -> Any:
        caller_id = ctx.caller_identity.id
        now = time.time()
        bucket_key = f"{self.key_prefix}:{caller_id}"

        sha = await self._load_script()

        # Execute Lua script atomically
        try:
            result = await self.redis.evalsha(  # type: ignore
                sha, 1, bucket_key, self.tokens_per_minute, now
            )
        except NoScriptError:
            # Script was flushed from Redis, reload and try again
            self._script_sha = None
            sha = await self._load_script()
            result = await self.redis.evalsha(  # type: ignore
                sha, 1, bucket_key, self.tokens_per_minute, now
            )

        if result == -1:
            raise RateLimitError("Rate limit exceeded")

        return await next_handler(inputs, ctx, descriptor)
