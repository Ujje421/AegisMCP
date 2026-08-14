import asyncio
import json

import pytest
from httpx import AsyncClient, ASGITransport
from starlette.testclient import TestClient

from aegismcp.adapters.starlette.transport import create_starlette_app
from aegismcp.server.app import AegisMCP


@pytest.mark.asyncio
async def test_starlette_transport_logic():
    from aegismcp.adapters.starlette.transport import ServerSseTransport
    from starlette.testclient import TestClient
    from starlette.routing import Route
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response, StreamingResponse

    transport = ServerSseTransport()
    
    async def message_endpoint(request: Request):
        body = await request.body()
        await transport.push_incoming(body.decode("utf-8"))
        return Response(status_code=202)
        
    app = Starlette(routes=[
        Route("/message", message_endpoint, methods=["POST"]),
    ])

    client = TestClient(app)
    
    # Test POSTing a message
    rpc_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "add",
            "arguments": {"a": 5, "b": 10}
        }
    }
    
    resp = client.post("/message", json=rpc_req)
    assert resp.status_code == 202
    
    # Verify the message went into the transport queue
    import json
    raw_msg = transport._queue.get_nowait()
    assert json.loads(raw_msg)["method"] == "tools/call"
    
    # Test that transport can send messages to the outbound queue
    from aegismcp.protocol.messages import JSONRPCRequest
    rpc_req_model = JSONRPCRequest(**rpc_req)
    await transport.send(rpc_req_model)
    outbound = transport.outbound_queue.get_nowait()
    assert json.loads(outbound)["method"] == "tools/call"

