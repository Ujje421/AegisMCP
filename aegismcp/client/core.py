import asyncio
from typing import Any

from aegismcp.kernel.errors import ConnectionError, ProtocolError
from aegismcp.kernel.events import EventBus
from aegismcp.kernel.ids import generate_request_id
from aegismcp.protocol.codec import ProtocolCodec
from aegismcp.protocol.lifecycle import SessionLifecycle, SessionState
from aegismcp.protocol.messages import JSONRPCNotification, JSONRPCRequest, JSONRPCResponse
from aegismcp.transports.base import Transport


class AegisClient:
    def __init__(self, transport: Transport):
        self.transport = transport
        self.codec = ProtocolCodec()
        self.bus = EventBus()
        self.lifecycle = SessionLifecycle(self.bus)

        self._pending_requests: dict[str | int, asyncio.Future[Any]] = {}
        self._receive_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        await self.transport.start()
        await self.lifecycle.transition_to(SessionState.READY)
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def disconnect(self) -> None:
        await self.lifecycle.transition_to(SessionState.CLOSING)
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        await self.transport.stop()
        await self.lifecycle.transition_to(SessionState.CLOSED)

        for future in self._pending_requests.values():
            if not future.done():
                future.set_exception(ConnectionError("Client disconnected"))
        self._pending_requests.clear()

    async def _receive_loop(self) -> None:
        try:
            async for message in self.transport.receive():
                await self._handle_message(message)
        except Exception as e:
            await self.bus.publish(ConnectionError(str(e)))

    async def _handle_message(self, message: Any) -> None:
        if isinstance(message, JSONRPCResponse):
            future = self._pending_requests.pop(message.id, None)
            if future and not future.done():
                if message.error:
                    msg = f"RPC Error {message.error.code}: {message.error.message}"
                    future.set_exception(ProtocolError(msg))
                else:
                    future.set_result(message.result)
        elif isinstance(message, JSONRPCNotification):
            # Future enhancement: emit to event bus
            pass

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        req_id = generate_request_id()
        request = JSONRPCRequest(
            id=req_id, method="tools/call", params={"name": name, "arguments": arguments}
        )

        loop = asyncio.get_running_loop()
        future: asyncio.Future[Any] = loop.create_future()
        self._pending_requests[req_id] = future

        await self.transport.send(request)
        return await future
