from datetime import UTC, datetime

import pytest

from aegismcp.agent.rag.base import Document, Embedder
from aegismcp.agent.rag.retriever import VectorRetriever, VectorStore
from aegismcp.kernel.context import create_anonymous_context


class MockEmbedder(Embedder):
    async def embed(self, text: str) -> list[float]:
        return [1.0, 0.0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class MockVectorStore(VectorStore):
    def __init__(self):
        self.docs = []

    async def search(self, vector: list[float], k: int) -> list[Document]:
        return self.docs[:k]

    async def insert(self, docs: list[Document], vectors: list[list[float]]) -> None:
        self.docs.extend(docs)


@pytest.mark.asyncio
async def test_vector_retriever():
    ctx = create_anonymous_context("r1", "t1", "s1", datetime.now(UTC))

    embedder = MockEmbedder()
    store = MockVectorStore()
    retriever = VectorRetriever(embedder, store)

    doc1 = Document("1", "Hello world", {})
    doc2 = Document("2", "Test doc", {})
    await store.insert([doc1, doc2], [[1.0, 0.0], [0.0, 1.0]])

    results = await retriever.retrieve("query", 1, ctx)
    assert len(results) == 1
    assert results[0].id == "1"
