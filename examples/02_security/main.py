import asyncio
from typing import Any
from aegismcp.server.app import AegisMCP
from aegismcp.security.auth.apikey import ApiKeyAuth
from aegismcp.security.policy.rbac import RBACPolicyEngine
from aegismcp.kernel.context import AegisContext

async def verify_key(key: str) -> dict[str, Any] | None:
    if key == "secret-admin":
        return {"id": "admin_user", "roles": ["admin"]}
    elif key == "secret-guest":
        return {"id": "guest_user", "roles": ["guest"]}
    return None

auth = ApiKeyAuth(verify_key)
policy = RBACPolicyEngine(role_permissions={
    "admin": frozenset(["system:read", "system:write"]),
    "guest": frozenset(["system:read"])
})

app = AegisMCP("SecureApp", auth=auth, policy=policy)

@app.tool(
    description="Read system data",
    required_permissions=frozenset(["system:read"])
)
async def read_data(ctx: AegisContext) -> str:
    return f"Data accessed by {ctx.caller_identity.id}"

@app.tool(
    description="Write system data",
    required_permissions=frozenset(["system:write"])
)
async def write_data(data: str, ctx: AegisContext) -> str:
    return f"Data '{data}' written by {ctx.caller_identity.id}"

if __name__ == "__main__":
    asyncio.run(app.run_stdio())
