import json
import logging
from typing import Any

from aegismcp.kernel.context import AegisContext


class StructuredJSONFormatter(logging.Formatter):
    """JSON formatter that injects standard attributes and context traces."""
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage()
        }
        
        if hasattr(record, "aegis_ctx"):
            ctx: AegisContext = getattr(record, "aegis_ctx")
            log_data.update({
                "request_id": ctx.request_id,
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id,
                "caller_id": ctx.caller_identity.id
            })
            
        return json.dumps(log_data)

def setup_json_logger(name: str = "aegismcp", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJSONFormatter())
        logger.addHandler(handler)
        
    return logger
