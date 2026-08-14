import httpx
import pytest

from aegismcp.protocol.codec import ProtocolCodec
from aegismcp.protocol.messages import JSONRPCRequest
from aegismcp.transports.http import HttpSseTransport


@pytest.mark.asyncio
async def test_http_transport(monkeypatch):
    codec = ProtocolCodec()
    
    class MockResponse:
        def raise_for_status(self): pass
        async def aiter_lines(self):
            yield "data: {\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"test\"}"
            yield "data:   "
            yield "invalid"
            yield "data: invalid"
            
    class MockStream:
        async def __aenter__(self):
            return MockResponse()
        async def __aexit__(self, *args):
            pass

    class MockAsyncClient:
        def stream(self, method, url):
            return MockStream()
        async def aclose(self):
            pass
        async def post(self, url, content, headers):
            class R:
                status_code = 200
            return R()
            
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    
    transport = HttpSseTransport("http://sse", "http://post", codec)
    await transport.start()
    
    msg = None
    async for m in transport.receive():
        msg = m
        break
        
    assert isinstance(msg, JSONRPCRequest)
    assert msg.id == 1
    
    await transport.send(JSONRPCRequest(id=2, method="foo"))
    await transport.stop()
