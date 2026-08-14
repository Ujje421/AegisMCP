from collections.abc import Callable
from dataclasses import dataclass

from aegismcp.kernel.types import PermissionSet


@dataclass
class ToolDescriptor:
    name: str
    description: str
    input_schema: dict
    output_schema: dict | None
    timeout_seconds: float
    max_retries: int
    retry_delay_seconds: float
    is_idempotent: bool
    required_permissions: PermissionSet
    audit_level: str
    fn: Callable
