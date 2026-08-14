from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from aegismcp.kernel.context import AegisContext
from aegismcp.kernel.errors import AegisError


class WorkflowError(AegisError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)

class Step(Protocol):
    name: str
    async def execute(self, *args: Any, ctx: AegisContext, **kwargs: Any) -> Any: ...
    async def compensate(self, *args: Any, ctx: AegisContext, **kwargs: Any) -> None: ...

@dataclass
class WorkflowExecution:
    workflow_name: str
    completed_steps: list[tuple[Step, tuple[Any, ...], dict[str, Any]]]

class WorkflowEngine:
    def __init__(self) -> None:
        self.workflows: dict[str, Callable[..., Awaitable[Any]]] = {}
    
    def register(self, name: str, fn: Callable[..., Awaitable[Any]]) -> None:
        self.workflows[name] = fn

    async def execute_saga(
        self, steps: list[tuple[Step, tuple[Any, ...], dict[str, Any]]], ctx: AegisContext
    ) -> list[Any]:
        execution = WorkflowExecution(workflow_name="saga", completed_steps=[])
        results = []
        
        try:
            for step, args, kwargs in steps:
                res = await step.execute(*args, ctx=ctx, **kwargs)
                results.append(res)
                execution.completed_steps.append((step, args, kwargs))
            return results
        except Exception as e:
            # Trigger compensation in reverse order
            for step, args, kwargs in reversed(execution.completed_steps):
                try:
                    await step.compensate(*args, ctx=ctx, **kwargs)
                except Exception:
                    pass
            raise WorkflowError(f"Saga execution failed and was compensated: {e}") from e
