import hashlib
import json
import time
from typing import Any

from aegismcp.execution.pipeline import ToolHandler
from aegismcp.kernel.context import AegisContext
from aegismcp.security.audit import AuditRecord, AuditSink
from aegismcp.security.policy.base import PolicyDecision
from aegismcp.tools.descriptor import ToolDescriptor


class AuditMiddleware:
    def __init__(self, sink: AuditSink):
        self.sink = sink
        
    async def __call__(
        self, 
        inputs: Any, 
        ctx: AegisContext, 
        descriptor: ToolDescriptor, 
        next_handler: ToolHandler
    ) -> Any:
        start_time = time.time()
        
        inputs_hash = None
        if inputs:
            try:
                inputs_str = json.dumps(inputs, sort_keys=True)
                inputs_hash = hashlib.sha256(inputs_str.encode()).hexdigest()
            except Exception:
                inputs_hash = "unhashable"
                
        outcome = "success"
        try:
            result = await next_handler(inputs, ctx, descriptor)
            return result
        except Exception:
            outcome = "error"
            raise
        finally:
            duration = (time.time() - start_time) * 1000
            
            record = AuditRecord(
                request_id=ctx.request_id,
                timestamp=start_time,
                caller_id=ctx.caller_identity.id,
                action="tool:call",
                resource=f"tool:{descriptor.name}",
                decision=PolicyDecision.ALLOW,
                inputs_hash=inputs_hash,
                outcome=outcome,
                duration_ms=duration
            )
            
            await self.sink.record(record)
