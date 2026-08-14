import asyncio
import sys
from collections.abc import AsyncIterator

from aegismcp.kernel.errors import ConnectionError
from aegismcp.protocol.codec import ProtocolCodec, RawMessage

from .base import Transport


class StdioTransport(Transport):
    def __init__(self, codec: ProtocolCodec):
        self._codec = codec
        self._running = False
        
    async def start(self) -> None:
        self._running = True
        
    async def stop(self) -> None:
        self._running = False
        
    async def receive(self) -> AsyncIterator[RawMessage]:
        loop = asyncio.get_running_loop()
        while self._running:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
                
            try:
                yield self._codec.decode(line)
            except Exception as e:
                raise ConnectionError(f"Failed to decode message: {e}")
                
    async def send(self, message: RawMessage) -> None:
        encoded = self._codec.encode(message)
        sys.stdout.write(encoded + "\n")
        sys.stdout.flush()
