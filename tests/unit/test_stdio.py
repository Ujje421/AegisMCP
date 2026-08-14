import sys

import pytest

from aegismcp.kernel.errors import ConnectionError
from aegismcp.protocol.codec import ProtocolCodec
from aegismcp.protocol.messages import JSONRPCRequest
from aegismcp.transports.stdio import StdioTransport


@pytest.mark.asyncio
async def test_stdio_transport(monkeypatch):
    codec = ProtocolCodec()
    transport = StdioTransport(codec)
    
    lines = ['{"jsonrpc": "2.0", "id": 1, "method": "test"}\n', "\n", ""]
    
    def mock_readline():
        return lines.pop(0)
        
    monkeypatch.setattr(sys.stdin, "readline", mock_readline)
    
    await transport.start()
    
    messages = []
    async for msg in transport.receive():
        messages.append(msg)
        
    assert len(messages) == 1
    assert isinstance(messages[0], JSONRPCRequest)
    
    await transport.stop()

@pytest.mark.asyncio
async def test_stdio_send(monkeypatch, capsys):
    codec = ProtocolCodec()
    transport = StdioTransport(codec)
    
    msg = JSONRPCRequest(id=1, method="test")
    await transport.send(msg)
    
    captured = capsys.readouterr()
    assert '"method":"test"' in captured.out
    
@pytest.mark.asyncio
async def test_stdio_invalid(monkeypatch):
    codec = ProtocolCodec()
    transport = StdioTransport(codec)
    
    lines = ["invalid json\n", ""]
    def mock_readline():
        return lines.pop(0)
        
    monkeypatch.setattr(sys.stdin, "readline", mock_readline)
    
    await transport.start()
    with pytest.raises(ConnectionError):
        async for msg in transport.receive():
            pass
