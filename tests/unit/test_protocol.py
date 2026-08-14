import pytest

from aegismcp.kernel.errors import InvalidMessageError
from aegismcp.protocol.codec import ProtocolCodec
from aegismcp.protocol.messages import JSONRPCNotification, JSONRPCRequest, JSONRPCResponse


def test_decode_request():
    codec = ProtocolCodec()
    msg = codec.decode('{"jsonrpc": "2.0", "id": 1, "method": "test"}')
    assert isinstance(msg, JSONRPCRequest)
    assert msg.id == 1
    assert msg.method == "test"

def test_encode_response():
    codec = ProtocolCodec()
    resp = JSONRPCResponse(id="req-1", result={"status": "ok"})
    encoded = codec.encode(resp)
    assert '"jsonrpc":"2.0"' in encoded
    assert '"id":"req-1"' in encoded
    assert '"result":{"status":"ok"}' in encoded

def test_decode_invalid():
    codec = ProtocolCodec()
    with pytest.raises(InvalidMessageError):
        codec.decode("invalid json")
        
def test_decode_invalid_jsonrpc():
    codec = ProtocolCodec()
    with pytest.raises(InvalidMessageError):
        codec.decode('{"jsonrpc": "1.0", "id": 1, "method": "test"}')
        
def test_decode_notification():
    codec = ProtocolCodec()
    msg = codec.decode('{"jsonrpc": "2.0", "method": "test_notify"}')
    assert isinstance(msg, JSONRPCNotification)
    assert msg.method == "test_notify"

def test_decode_invalid_type():
    codec = ProtocolCodec()
    with pytest.raises(InvalidMessageError):
        codec.decode('["array", "instead", "of", "object"]')

def test_decode_invalid_request():
    codec = ProtocolCodec()
    msg = codec.decode('{"jsonrpc": "2.0", "id": 1}') # missing method, parsed as response
    assert isinstance(msg, JSONRPCResponse)

def test_decode_missing_method_and_id():
    codec = ProtocolCodec()
    with pytest.raises(InvalidMessageError):
        codec.decode('{"jsonrpc": "2.0"}')
