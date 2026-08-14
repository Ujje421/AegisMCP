from collections.abc import Callable
from typing import Any

from aegismcp.protocol.codec import ProtocolCodec
from aegismcp.tools.decorator import tool
from aegismcp.tools.descriptor import ToolDescriptor
from aegismcp.transports.stdio import StdioTransport


class AegisMCP:
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = ""
    ):
        self.name = name
        self.version = version
        self.description = description
        self.tools: dict[str, ToolDescriptor] = {}
        
    def tool(self, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a tool. Delegates to the @tool decorator."""
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            decorated_fn = tool(**kwargs)(fn)
            descriptor = getattr(decorated_fn, "__aegis_tool__")
            self.tools[descriptor.name] = descriptor
            return decorated_fn
        return decorator
        
    async def run_stdio(self) -> None:
        """Run the server using stdio transport."""
        codec = ProtocolCodec()
        transport = StdioTransport(codec)
        await transport.start()
        
        try:
            async for message in transport.receive():
                # To be implemented with proper execution pipeline
                pass
        finally:
            await transport.stop()
