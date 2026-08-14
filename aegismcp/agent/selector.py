from typing import Protocol

from aegismcp.tools.descriptor import ToolDescriptor

from .models import Message


class ToolSelector(Protocol):
    async def select(
        self,
        messages: list[Message],
        registry: dict[str, ToolDescriptor],
        max_tools: int = 20,
    ) -> list[ToolDescriptor]: ...


class AllToolsSelector(ToolSelector):
    async def select(
        self,
        messages: list[Message],
        registry: dict[str, ToolDescriptor],
        max_tools: int = 20,
    ) -> list[ToolDescriptor]:
        return list(registry.values())[:max_tools]
