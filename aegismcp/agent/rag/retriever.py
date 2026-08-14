from typing import Protocol

from aegismcp.kernel.context import AegisContext

from .base import Document, Embedder


class Retriever(Protocol):
    async def retrieve(self, query: str, k: int, ctx: AegisContext) -> list[Document]: ...


class VectorStore(Protocol):
    async def search(self, vector: list[float], k: int) -> list[Document]: ...
    async def insert(self, docs: list[Document], vectors: list[list[float]]) -> None: ...


class VectorRetriever(Retriever):
    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store

    async def retrieve(self, query: str, k: int, ctx: AegisContext) -> list[Document]:
        query_vec = await self.embedder.embed(query)
        return await self.store.search(query_vec, k)
