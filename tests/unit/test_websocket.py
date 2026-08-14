import asyncio

import pytest
import websockets

from aegismcp.protocol.codec import ProtocolCodec
from aegismcp.protocol.messages import JSONRPCRequest
from aegismcp.transports.websocket import WebSocketTransport


@pytest.mark.asyncio
async def test_websocket_transport(monkeypatch):
    codec = ProtocolCodec()
    
    class MockWS:
        def __init__(self):
            self.msgs = []
        async def recv(self):
            if not self.msgs:
                await asyncio.sleep(0.01)
                # Just raise a standard exception for testing
                # instead of finding the exact websockets one
                raise Exception("closed")
            return self.msgs.pop(0)
        async def send(self, msg):
            self.msgs.append(msg)
        async def close(self):
            pass
            
    async def mock_connect(url):
        ws = MockWS()
        ws.msgs.append('{"jsonrpc": "2.0", "id": 1, "method": "test"}')
        ws.msgs.append('invalid json')
        return ws
        
    monkeypatch.setattr(websockets, "connect", mock_connect)
    
    transport = WebSocketTransport("ws://test", codec)
    await transport.start()
    
    messages = []
    async for msg in transport.receive():
        messages.append(msg)
        
    assert len(messages) == 1
    assert isinstance(messages[0], JSONRPCRequest)
    assert messages[0].id == 1
    
    await transport.send(JSONRPCRequest(id=2, method="foo"))
    
    await transport.stop()
