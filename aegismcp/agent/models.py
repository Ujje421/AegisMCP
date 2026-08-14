from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

from aegismcp.kernel.context import AegisContext
from aegismcp.tools.descriptor import ToolDescriptor


@dataclass(frozen=True)
class Message:
    role: str
    content: str

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        return cls(role="assistant", content=content)

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role="system", content=content)

    @classmethod
    def tool(cls, content: str) -> "Message":
        return cls(role="tool", content=content)


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelResponse:
    content: str
    tool_calls: list[ToolCall]

    def as_assistant_message(self) -> Message:
        return Message.assistant(self.content)


@dataclass(frozen=True)
class ModelResponseChunk:
    content_delta: str


@dataclass(frozen=True)
class GenerationConfig:
    max_tokens: int = 1000
    temperature: float = 0.7


class ModelProvider(Protocol):
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDescriptor],
        config: GenerationConfig,
        ctx: AegisContext,
    ) -> ModelResponse: ...

    def stream(
        self,
        messages: list[Message],
        tools: list[ToolDescriptor],
        config: GenerationConfig,
        ctx: AegisContext,
    ) -> AsyncIterator[ModelResponseChunk]: ...
