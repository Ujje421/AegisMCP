import asyncio
from collections.abc import AsyncIterator

import httpx

from aegismcp.kernel.errors import ConnectionError
from aegismcp.protocol.codec import ProtocolCodec, RawMessage
from aegismcp.transports.base import Transport


class HttpSseTransport(Transport):
    def __init__(self, sse_url: str, post_url: str, codec: ProtocolCodec):
        self.sse_url = sse_url
        self.post_url = post_url
        self._codec = codec
        self._client = httpx.AsyncClient()
        self._running = False
        self._queue: asyncio.Queue[RawMessage] = asyncio.Queue()
        self._receive_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._running = True
        self._receive_task = asyncio.create_task(self._listen_sse())

    async def _listen_sse(self) -> None:
        try:
            async with self._client.stream("GET", self.sse_url) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not self._running:
                        break
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip():
                            try:
                                msg = self._codec.decode(data)
                                await self._queue.put(msg)
                            except Exception:
                                pass
        except Exception:
            if self._running:
                self._running = False

    async def stop(self) -> None:
        self._running = False
        if self._receive_task:
            self._receive_task.cancel()
        await self._client.aclose()

    async def receive(self) -> AsyncIterator[RawMessage]:
        while self._running:
            try:
                msg = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                yield msg
            except TimeoutError:
                continue

    async def send(self, message: RawMessage) -> None:
        encoded = self._codec.encode(message)
        response = await self._client.post(
            self.post_url, content=encoded, headers={"Content-Type": "application/json"}
        )
        if response.status_code >= 400:
            raise ConnectionError(f"HTTP Error {response.status_code}: {response.text}")
