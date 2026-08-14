from collections.abc import Awaitable, Callable
from typing import Any


class WorkflowRegistry:
    def __init__(self) -> None:
        self.workflows: dict[str, Callable[..., Awaitable[Any]]] = {}
    def workflow(self, name: str | None = None) -> Callable[
        [Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]
    ]:
        def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            wf_name = name or fn.__name__
            self.workflows[wf_name] = fn
            return fn
        return decorator
