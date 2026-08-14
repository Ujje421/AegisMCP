from typing import Any, Protocol

from aegismcp.kernel.context import AegisContext


class Memory(Protocol):
    async def store(self, key: str, value: Any, ctx: AegisContext) -> None: ...
    async def retrieve(self, key: str, ctx: AegisContext) -> Any | None: ...


class InMemoryMemory(Memory):
    def __init__(self) -> None:
        self.storage: dict[str, Any] = {}

    async def store(self, key: str, value: Any, ctx: AegisContext) -> None:
        self.storage[key] = value

    async def retrieve(self, key: str, ctx: AegisContext) -> Any | None:
        return self.storage.get(key)
