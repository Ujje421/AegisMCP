import asyncio

import pytest

from aegismcp.client.core import AegisClient
from aegismcp.client.pool import ConnectionPool
from aegismcp.protocol.messages import JSONRPCResponse


@pytest.mark.asyncio
async def test_aegis_client(monkeypatch):
    class MockTransport:
        def __init__(self):
            self.msgs = []
            self.event = asyncio.Event()

        async def start(self):
            pass

        async def stop(self):
            pass

        async def receive(self):
            await self.event.wait()
            yield JSONRPCResponse(id="test-1", result={"foo": "bar"})

        async def send(self, msg):
            self.msgs.append(msg)
            self.event.set()

    transport = MockTransport()
    client = AegisClient(transport)  # type: ignore
    await client.connect()

    import aegismcp.client.core

    monkeypatch.setattr(aegismcp.client.core, "generate_request_id", lambda: "test-1")

    res = await client.call_tool("my_tool", {"a": 1})
    assert res == {"foo": "bar"}
    assert len(transport.msgs) == 1

    await client.disconnect()


@pytest.mark.asyncio
async def test_connection_pool():
    pool = ConnectionPool(size=2)

    class DummyClient:
        async def connect(self):
            pass

        async def disconnect(self):
            pass

    c1 = DummyClient()
    c2 = DummyClient()

    await pool.add_client(c1)  # type: ignore
    await pool.add_client(c2)  # type: ignore

    assert await pool.get_client() is c1
    assert await pool.get_client() is c2
    assert await pool.get_client() is c1

    await pool.close()
