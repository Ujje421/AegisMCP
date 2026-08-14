import time
from typing import Any

from aegismcp.execution.pipeline import ToolHandler
from aegismcp.kernel.context import AegisContext
from aegismcp.observability.metrics import MetricsProvider
from aegismcp.observability.tracing import TracerProvider
from aegismcp.tools.descriptor import ToolDescriptor


class ObservabilityMiddleware:
    def __init__(self, metrics: MetricsProvider, tracer: TracerProvider):
        self.metrics = metrics
        self.tracer = tracer
        
        self.calls_counter = self.metrics.create_counter(
            name="aegismcp.tool.calls",
            description="Number of tool calls"
        )
        self.duration_histogram = self.metrics.create_histogram(
            name="aegismcp.tool.duration",
            description="Duration of tool calls in milliseconds"
        )
        self.errors_counter = self.metrics.create_counter(
            name="aegismcp.tool.errors",
            description="Number of tool execution errors"
        )
        
    async def __call__(
        self, 
        inputs: Any, 
        ctx: AegisContext, 
        descriptor: ToolDescriptor, 
        next_handler: ToolHandler
    ) -> Any:
        span_name = f"aegismcp.tool.{descriptor.name}"
        span = self.tracer.start_span(span_name)
        
        start_time = time.time()
        
        with span:
            span.set_attribute("request_id", ctx.request_id)
            span.set_attribute("trace_id", ctx.trace_id)
            span.set_attribute("tool_name", descriptor.name)
            span.set_attribute("caller_id", ctx.caller_identity.id)
            
            try:
                result = await next_handler(inputs, ctx, descriptor)
                
                duration_ms = (time.time() - start_time) * 1000
                self.calls_counter.add(1, {"tool_name": descriptor.name, "outcome": "success"})
                self.duration_histogram.record(duration_ms, {"tool_name": descriptor.name})
                span.set_status("OK")
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.calls_counter.add(1, {"tool_name": descriptor.name, "outcome": "error"})
                self.errors_counter.add(
                    1, 
                    {"tool_name": descriptor.name, "error_type": type(e).__name__}
                )
                self.duration_histogram.record(duration_ms, {"tool_name": descriptor.name})
                span.set_status("ERROR", str(e))
                raise
