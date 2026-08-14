import json
import logging
from datetime import UTC, datetime

import pytest

from aegismcp.execution.middleware.observability import ObservabilityMiddleware
from aegismcp.kernel.context import create_anonymous_context
from aegismcp.observability.logging import StructuredJSONFormatter
from aegismcp.observability.metrics import InMemoryMetricsProvider
from aegismcp.observability.tracing import InMemoryTracerProvider
from aegismcp.tools.descriptor import ToolDescriptor


@pytest.mark.asyncio
async def test_observability_middleware():
    metrics = InMemoryMetricsProvider()
    tracer = InMemoryTracerProvider()
    mw = ObservabilityMiddleware(metrics, tracer)
    
    desc = ToolDescriptor(
        name="test_tool", description="", input_schema={}, output_schema=None,
        timeout_seconds=5.0, max_retries=0, retry_delay_seconds=0, is_idempotent=False,
        required_permissions=frozenset(), audit_level="NONE", fn=lambda: 1
    )
    ctx = create_anonymous_context("req1", "t1", "s1", datetime.now(UTC))
    
    async def mock_handler(inputs, ctx, desc):
        return "success"
        
    res = await mw({}, ctx, desc, mock_handler)
    assert res == "success"
    
    assert "aegismcp.tool.calls" in metrics.counters
    assert metrics.counters["aegismcp.tool.calls"].value == 1.0
    assert "aegismcp.tool.duration" in metrics.histograms
    assert len(metrics.histograms["aegismcp.tool.duration"].records) == 1
    
    assert len(tracer.spans) == 1
    span = tracer.spans[0]
    assert span.name == "aegismcp.tool.test_tool"
    assert span.status == "OK"
    assert span.attributes["trace_id"] == "t1"
    
    # Error case
    async def error_handler(inputs, ctx, desc):
        raise ValueError("fail")
        
    with pytest.raises(ValueError):
        await mw({}, ctx, desc, error_handler)
        
    assert metrics.counters["aegismcp.tool.calls"].value == 2.0
    assert metrics.counters["aegismcp.tool.errors"].value == 1.0
    assert tracer.spans[1].status == "ERROR"

def test_json_logger():
    formatter = StructuredJSONFormatter()
    record = logging.LogRecord("test_logger", logging.INFO, "path", 1, "msg", (), None)
    ctx = create_anonymous_context("r", "t", "s", datetime.now(UTC))
    setattr(record, "aegis_ctx", ctx)
    
    output = formatter.format(record)
    data = json.loads(output)
    
    assert data["message"] == "msg"
    assert data["level"] == "INFO"
    assert data["request_id"] == "r"
    assert data["trace_id"] == "t"
