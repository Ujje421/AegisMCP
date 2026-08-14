import asyncio
from typing import Any

from aegismcp.kernel.context import AegisContext, Identity
from aegismcp.security.auth.apikey import ApiKeyAuth
from aegismcp.security.policy.rbac import RBACPolicyEngine
from aegismcp.server.app import AegisMCP


class RoleBasedApiKeyAuth(ApiKeyAuth):
    async def authenticate(self, request: Any) -> Identity | None:
        if not isinstance(request, dict):
            return None
        token = request.get("api_key")
        if token == "secret-admin":
            return Identity(id="admin_user", type="api_key", attributes={"roles": ["admin"]})
        elif token == "secret-guest":
            return Identity(id="guest_user", type="api_key", attributes={"roles": ["guest"]})
        return None


auth = RoleBasedApiKeyAuth(keys=set())
policy = RBACPolicyEngine(
    role_permissions={"admin": {"system:read", "system:write"}, "guest": {"system:read"}}
)

app = AegisMCP("SecureApp", auth=auth, policy=policy)


@app.tool(description="Read system data", required_permissions=frozenset(["system:read"]))
async def read_data(ctx: AegisContext) -> str:
    return f"Data accessed by {ctx.caller_identity.id}"


@app.tool(description="Write system data", required_permissions=frozenset(["system:write"]))
async def write_data(data: str, ctx: AegisContext) -> str:
    return f"Data '{data}' written by {ctx.caller_identity.id}"


if __name__ == "__main__":
    asyncio.run(app.run_stdio())
