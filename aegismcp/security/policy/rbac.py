from aegismcp.kernel.context import AegisContext, Identity

from .base import PolicyDecision, PolicyEngine


class RBACPolicyEngine(PolicyEngine):
    def __init__(self, role_permissions: dict[str, set[str]]):
        self.role_permissions = role_permissions

    async def evaluate(
        self,
        identity: Identity,
        action: str,
        resource: str,
        ctx: AegisContext,
    ) -> tuple[PolicyDecision, str | None]:
        roles = identity.attributes.get("roles", [])
        if not isinstance(roles, list):
            return PolicyDecision.DENY, "Invalid roles format"

        for role in roles:
            if role in self.role_permissions:
                if action in self.role_permissions[role]:
                    return PolicyDecision.ALLOW, None

        return PolicyDecision.DENY, f"Missing required permission: {action}"
