from collections.abc import Callable
from typing import Any

from aegismcp.execution.executor import ToolExecutor
from aegismcp.execution.pipeline import ExecutionPipeline
from aegismcp.protocol.codec import ProtocolCodec
from aegismcp.tools.decorator import tool
from aegismcp.tools.descriptor import ToolDescriptor
from aegismcp.transports.stdio import StdioTransport


class AegisMCP:
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        auth: Any = None,
        policy: Any = None,
        audit: Any = None,
        rate_limit: int | None = None,
        telemetry_metrics: Any = None,
        telemetry_tracer: Any = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.tools: dict[str, ToolDescriptor] = {}

        from aegismcp.workflow.engine import WorkflowEngine

        self.workflow_engine = WorkflowEngine()

        from aegismcp.execution.pipeline import Middleware
        self.middlewares: list[Middleware] = []
        if telemetry_metrics and telemetry_tracer:
            from aegismcp.execution.middleware.observability import ObservabilityMiddleware

            self.middlewares.append(ObservabilityMiddleware(telemetry_metrics, telemetry_tracer))
        if rate_limit is not None:
            from aegismcp.execution.middleware.ratelimit import RateLimitMiddleware

            self.middlewares.append(RateLimitMiddleware(rate_limit))
        if auth:
            from aegismcp.execution.middleware.auth import AuthenticationMiddleware

            self.middlewares.append(AuthenticationMiddleware(auth))
        if policy:
            from aegismcp.execution.middleware.auth import AuthorizationMiddleware

            self.middlewares.append(AuthorizationMiddleware(policy))
        if audit:
            from aegismcp.execution.middleware.audit import AuditMiddleware

            self.middlewares.append(AuditMiddleware(audit))

        self.executor = ToolExecutor()
        self.pipeline = ExecutionPipeline(self.middlewares, self.executor)

    def tool(self, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a tool. Delegates to the @tool decorator."""

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            decorated_fn: Callable[..., Any] = tool(**kwargs)(fn)
            descriptor = getattr(decorated_fn, "__aegis_tool__")
            self.tools[descriptor.name] = descriptor
            return decorated_fn

        return decorator

    def workflow(self, name: str | None = None) -> Any:
        def decorator(fn: Any) -> Any:
            wf_name = name or fn.__name__
            self.workflow_engine.register(wf_name, fn)
            return fn

        return decorator

    async def run_stdio(self) -> None:
        """Run the server using stdio transport."""
        codec = ProtocolCodec()
        transport = StdioTransport(codec)
        await transport.start()

        try:
            async for message in transport.receive():
                # To be implemented with proper execution pipeline
                pass
        finally:
            await transport.stop()
