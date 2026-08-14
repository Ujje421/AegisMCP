import pytest
from aegismcp.server.app import AegisMCP

@pytest.mark.asyncio
async def test_app_tool_registration():
    app = AegisMCP("TestApp", "1.0")
    
    @app.tool(description="A test tool")
    def my_tool(x: int) -> int:
        return x
        
    assert "my_tool" in app.tools
    assert app.tools["my_tool"].description == "A test tool"

@pytest.mark.asyncio
async def test_app_run_stdio(monkeypatch):
    app = AegisMCP("TestApp")
    
    class MockTransport:
        def __init__(self, codec): pass
        async def start(self): pass
        async def stop(self): pass
        async def receive(self):
            yield "msg"
            
    from aegismcp.server import app as app_module
    monkeypatch.setattr(app_module, "StdioTransport", MockTransport)
    
    await app.run_stdio()
