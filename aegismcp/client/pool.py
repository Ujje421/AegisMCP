import asyncio

from aegismcp.kernel.errors import ConnectionError

from .core import AegisClient


class ConnectionPool:
    def __init__(self, size: int = 5):
        self.size = size
        self.clients: list[AegisClient] = []
        self._lock = asyncio.Lock()
        self._index = 0
        
    async def add_client(self, client: AegisClient) -> None:
        async with self._lock:
            if len(self.clients) >= self.size:
                raise ConnectionError("Pool is full")
            self.clients.append(client)
            await client.connect()
            
    async def get_client(self) -> AegisClient:
        async with self._lock:
            if not self.clients:
                raise ConnectionError("No clients available in pool")
            
            # Simple round-robin
            client = self.clients[self._index]
            self._index = (self._index + 1) % len(self.clients)
            return client
            
    async def close(self) -> None:
        async with self._lock:
            for client in self.clients:
                await client.disconnect()
            self.clients.clear()
