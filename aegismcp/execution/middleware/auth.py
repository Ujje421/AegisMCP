from dataclasses import replace
from typing import Any

from aegismcp.execution.pipeline import ToolHandler
from aegismcp.kernel.context import AegisContext
from aegismcp.kernel.errors import AuthenticationError, AuthorizationError
from aegismcp.security.auth.base import AuthStrategy
from aegismcp.security.policy.base import PolicyDecision, PolicyEngine
from aegismcp.tools.descriptor import ToolDescriptor


class AuthenticationMiddleware:
    def __init__(self, strategy: AuthStrategy):
        self.strategy = strategy

    async def __call__(
        self, inputs: Any, ctx: AegisContext, descriptor: ToolDescriptor, next_handler: ToolHandler
    ) -> Any:
        identity = await self.strategy.authenticate(ctx.metadata)
        if not identity:
            raise AuthenticationError("Authentication failed")

        new_ctx = replace(ctx, caller_identity=identity)
        return await next_handler(inputs, new_ctx, descriptor)


class AuthorizationMiddleware:
    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    async def __call__(
        self, inputs: Any, ctx: AegisContext, descriptor: ToolDescriptor, next_handler: ToolHandler
    ) -> Any:
        for permission in descriptor.required_permissions:
            decision, reason = await self.policy_engine.evaluate(
                identity=ctx.caller_identity,
                action=permission,
                resource=f"tool:{descriptor.name}",
                ctx=ctx,
            )

            if decision != PolicyDecision.ALLOW:
                raise AuthorizationError(f"Access denied: {reason or 'Insufficient permissions'}")

        return await next_handler(inputs, ctx, descriptor)
