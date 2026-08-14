from typing import Any, Protocol

from aegismcp.kernel.context import Identity


class AuthStrategy(Protocol):
    """
    Protocol for authentication strategies.
    Takes a raw transport message/request and returns an Identity if authenticated.
    Raises AuthenticationError if authentication fails.
    """

    async def authenticate(self, request: Any) -> Identity | None: ...
