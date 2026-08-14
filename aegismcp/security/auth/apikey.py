from typing import Any

from aegismcp.kernel.context import Identity
from aegismcp.kernel.errors import AuthenticationError

from .base import AuthStrategy


class ApiKeyAuth(AuthStrategy):
    def __init__(self, keys: set[str]):
        self.keys = keys

    async def authenticate(self, request: Any) -> Identity | None:
        if not isinstance(request, dict):
            return None

        token = (
            request.get("api_key") or request.get("Authorization") or request.get("authorization")
        )
        if not token:
            raise AuthenticationError("Missing API key")

        if isinstance(token, str) and token.startswith("Bearer "):
            token = token[7:]

        if token not in self.keys:
            raise AuthenticationError("Invalid API key")

        return Identity(id="api_user", type="api_key")
