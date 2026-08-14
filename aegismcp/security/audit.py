from dataclasses import dataclass
from typing import Protocol

from .policy.base import PolicyDecision


@dataclass(frozen=True)
class AuditRecord:
    request_id: str
    timestamp: float
    caller_id: str
    action: str
    resource: str
    decision: PolicyDecision
    inputs_hash: str | None
    outcome: str
    duration_ms: float


class AuditSink(Protocol):
    async def record(self, record: AuditRecord) -> None: ...


class LoggerAuditSink(AuditSink):
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    async def record(self, record: AuditRecord) -> None:
        self.records.append(record)
