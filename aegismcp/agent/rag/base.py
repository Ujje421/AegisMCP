from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Document:
    id: str
    content: str
    metadata: dict[str, str | int | float]

class Embedder(Protocol):
    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

class Chunker(Protocol):
    def chunk(self, text: str) -> list[str]: ...
