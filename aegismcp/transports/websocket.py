from collections.abc import AsyncIterator
from typing import Any

import websockets

from aegismcp.kernel.errors import ConnectionError
from aegismcp.protocol.codec import ProtocolCodec, RawMessage
from aegismcp.transports.base import Transport


class WebSocketTransport(Transport):
    def __init__(self, url: str, codec: ProtocolCodec):
        self.url = url
        self._codec = codec
        # type ignore because websockets typing can be complex
        self._connection: Any | None = None  # type: ignore
        self._running = False

    async def start(self) -> None:
        try:
            self._connection = await websockets.connect(self.url)  # type: ignore
            self._running = True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to WebSocket: {e}")

    async def stop(self) -> None:
        self._running = False
        if self._connection:
            await self._connection.close()  # type: ignore

    async def receive(self) -> AsyncIterator[RawMessage]:
        if not self._connection:
            raise ConnectionError("WebSocket not connected")

        while self._running:
            try:
                message = await self._connection.recv()  # type: ignore
                yield self._codec.decode(message)
            except Exception:
                self._running = False
                break

    async def send(self, message: RawMessage) -> None:
        if not self._connection:
            raise ConnectionError("WebSocket not connected")

        encoded = self._codec.encode(message)
        await self._connection.send(encoded)  # type: ignore
