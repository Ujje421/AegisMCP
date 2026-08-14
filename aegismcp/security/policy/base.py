from enum import Enum
from typing import Protocol

from aegismcp.kernel.context import AegisContext, Identity


class PolicyDecision(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    DENY_WITH_REASON = "DENY_WITH_REASON"

class PolicyEngine(Protocol):
    async def evaluate(
        self,
        identity: Identity,
        action: str,
        resource: str,
        ctx: AegisContext,
    ) -> tuple[PolicyDecision, str | None]: ...
