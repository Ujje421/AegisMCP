from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from aegismcp.kernel.context import AegisContext
from aegismcp.tools.descriptor import ToolDescriptor

ToolHandler = Callable[[Any, AegisContext, ToolDescriptor], Awaitable[Any]]


class Middleware(Protocol):
    async def __call__(
        self, inputs: Any, ctx: AegisContext, descriptor: ToolDescriptor, next_handler: ToolHandler
    ) -> Any: ...


class ExecutionPipeline:
    def __init__(self, middlewares: list[Middleware], executor: ToolHandler):
        self._middlewares = middlewares
        self._executor = executor
        self._chain = self._build_chain()

    def _build_chain(self) -> ToolHandler:
        chain = self._executor
        # Type ignored because we capture variables in the loop closure manually
        for middleware in reversed(self._middlewares):

            def wrap(mw: Middleware = middleware, nxt: ToolHandler = chain) -> ToolHandler:
                async def wrapped(
                    inputs: Any, ctx: AegisContext, descriptor: ToolDescriptor
                ) -> Any:
                    return await mw(inputs, ctx, descriptor, nxt)

                return wrapped

            chain = wrap()
        return chain

    async def execute(self, inputs: Any, ctx: AegisContext, descriptor: ToolDescriptor) -> Any:
        return await self._chain(inputs, ctx, descriptor)
