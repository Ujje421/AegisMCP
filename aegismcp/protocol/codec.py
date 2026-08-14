import json

from aegismcp.kernel.errors import InvalidMessageError

from .messages import JSONRPCNotification, JSONRPCRequest, JSONRPCResponse

RawMessage = JSONRPCRequest | JSONRPCResponse | JSONRPCNotification

class ProtocolCodec:
    def decode(self, data: str | bytes) -> RawMessage:
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            raise InvalidMessageError(f"Invalid JSON: {e}")
            
        if not isinstance(parsed, dict):
            raise InvalidMessageError("JSON-RPC message must be an object")
            
        if parsed.get("jsonrpc") != "2.0":
            raise InvalidMessageError("Invalid jsonrpc version")
            
        if "id" in parsed:
            if "method" in parsed:
                return JSONRPCRequest(**parsed)
            else:
                return JSONRPCResponse(**parsed)
        else:
            if "method" in parsed:
                return JSONRPCNotification(**parsed)
            else:
                raise InvalidMessageError("Invalid JSON-RPC message structure")

    def encode(self, message: RawMessage) -> str:
        return message.model_dump_json(exclude_none=True)
