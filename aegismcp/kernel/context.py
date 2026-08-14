from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, TypeVar

from .types import FrozenMapping, PermissionSet

T = TypeVar("T")

@dataclass(frozen=True)
class Identity:
    """Represents the authenticated caller identity."""
    id: str
    type: str  # e.g., "user", "service", "anonymous"
    attributes: FrozenMapping = field(default_factory=dict)

@dataclass(frozen=True)
class AegisContext:
    """
    The frozen, explicitly-propagated value object that carries request state.
    
    This solves tracing, security, testing, and debugging simultaneously.
    """
    request_id: str
    trace_id: str
    span_id: str
    caller_identity: Identity
    permissions: PermissionSet
    deadline: datetime
    metadata: FrozenMapping
    baggage: FrozenMapping

    def with_deadline(self, new_deadline: datetime) -> "AegisContext":
        """Return a new context with a tighter deadline (cannot extend)."""
        if new_deadline > self.deadline:
            # Can only tighten deadlines, not extend them
            return self
        return replace(self, deadline=new_deadline)
        
    def with_span(self, new_span_id: str) -> "AegisContext":
        """Return a new context with a new span ID for tracing sub-operations."""
        return replace(self, span_id=new_span_id)
        
    def with_metadata(self, new_metadata: Mapping[str, Any]) -> "AegisContext":
        """Return a new context with merged metadata."""
        merged = dict(self.metadata)
        merged.update(new_metadata)
        return replace(self, metadata=merged)

def create_anonymous_context(
    request_id: str, 
    trace_id: str, 
    span_id: str, 
    deadline: datetime
) -> AegisContext:
    """Create a context for an unauthenticated request."""
    return AegisContext(
        request_id=request_id,
        trace_id=trace_id,
        span_id=span_id,
        caller_identity=Identity(id="anonymous", type="anonymous", attributes={}),
        permissions=frozenset(),
        deadline=deadline,
        metadata={},
        baggage={}
    )
