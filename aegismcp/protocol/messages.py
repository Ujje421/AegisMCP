from typing import Any, Literal

from pydantic import BaseModel


class JSONRPCMessage(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"

class JSONRPCRequest(JSONRPCMessage):
    id: str | int
    method: str
    params: dict[str, Any] | None = None

class JSONRPCNotification(JSONRPCMessage):
    method: str
    params: dict[str, Any] | None = None

class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Any | None = None

class JSONRPCResponse(JSONRPCMessage):
    id: str | int
    result: Any | None = None
    error: JSONRPCError | None = None
