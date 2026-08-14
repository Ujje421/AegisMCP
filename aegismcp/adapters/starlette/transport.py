import asyncio
from typing import Any
from collections.abc import AsyncGenerator

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route

from aegismcp.protocol.codec import ProtocolCodec
from aegismcp.server.app import AegisMCP
from aegismcp.transports.base import Transport


# Simple SSE Response for Starlette
class EventSourceResponse(StreamingResponse):
    media_type = "text/event-stream"

    def __init__(self, content: Any, **kwargs: Any) -> None:
        super().__init__(content, **kwargs)
        self.headers["Cache-Control"] = "no-cache"
        self.headers["Connection"] = "keep-alive"


class ServerSseTransport(Transport):
    """
    A transport that binds AegisMCP to an incoming Starlette request flow.
    Unlike standard transports that pull from sockets, this transport
    is pushed to by Starlette POST requests, and yields to the Aegis engine.
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._codec = ProtocolCodec()
        self.outbound_queue: asyncio.Queue[str] = asyncio.Queue()

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def receive(self) -> AsyncGenerator[Any, None]:
        while True:
            raw_msg = await self._queue.get()
            try:
                yield self._codec.decode(raw_msg)
            except Exception as e:
                print(f"DEBUG: Transport decode failed: {e}")

    async def send(self, message: Any) -> None:
        encoded = self._codec.encode(message)
        await self.outbound_queue.put(encoded)

    async def push_incoming(self, raw_data: str) -> None:
        await self._queue.put(raw_data)


from contextlib import asynccontextmanager


def create_starlette_app(aegis_app: AegisMCP) -> Starlette:
    """
    Creates a Starlette ASGI application that mounts the given AegisMCP instance.
    """
    transport = ServerSseTransport()

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncGenerator[None, None]:
        task = asyncio.create_task(aegis_app.run_transport(transport))
        yield
        task.cancel()

    async def sse_endpoint(request: Request) -> Response:
        async def event_generator() -> AsyncGenerator[bytes, None]:
            while True:
                msg = await transport.outbound_queue.get()
                yield f"data: {msg}\n\n".encode("utf-8")

        return EventSourceResponse(event_generator())

    async def message_endpoint(request: Request) -> Response:
        body = await request.body()
        await transport.push_incoming(body.decode("utf-8"))
        return Response(status_code=202)

    routes = [
        Route("/sse", sse_endpoint, methods=["GET"]),
        Route("/message", message_endpoint, methods=["POST"]),
    ]

    return Starlette(routes=routes, lifespan=lifespan)
