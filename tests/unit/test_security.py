from datetime import UTC, datetime

import pytest

from aegismcp.execution.middleware.audit import AuditMiddleware
from aegismcp.execution.middleware.auth import AuthenticationMiddleware, AuthorizationMiddleware
from aegismcp.execution.middleware.ratelimit import RateLimitError, RateLimitMiddleware
from aegismcp.kernel.context import Identity, create_anonymous_context
from aegismcp.security.audit import LoggerAuditSink
from aegismcp.security.auth.apikey import ApiKeyAuth
from aegismcp.security.policy.base import PolicyDecision
from aegismcp.security.policy.rbac import RBACPolicyEngine
from aegismcp.tools.descriptor import ToolDescriptor


@pytest.mark.asyncio
async def test_apikey_auth():
    auth = ApiKeyAuth({"secret-123"})
    
    with pytest.raises(Exception):
        await auth.authenticate({})
        
    with pytest.raises(Exception):
        await auth.authenticate({"api_key": "bad"})
        
    ident = await auth.authenticate({"api_key": "secret-123"})
    assert ident is not None
    assert ident.id == "api_user"
    
    # Bearer token
    ident = await auth.authenticate({"Authorization": "Bearer secret-123"})
    assert ident is not None

@pytest.mark.asyncio
async def test_rbac_policy():
    engine = RBACPolicyEngine({"admin": {"read", "write"}, "user": {"read"}})
    ctx = create_anonymous_context("req1", "t1", "s1", datetime.now(UTC))
    
    ident = Identity("user1", "user", {"roles": ["guest"]})
    decision, _ = await engine.evaluate(ident, "read", "res1", ctx)
    assert decision == PolicyDecision.DENY
    
    ident = Identity("user1", "user", {"roles": ["user"]})
    decision, _ = await engine.evaluate(ident, "read", "res1", ctx)
    assert decision == PolicyDecision.ALLOW
    
    decision, _ = await engine.evaluate(ident, "write", "res1", ctx)
    assert decision == PolicyDecision.DENY

@pytest.mark.asyncio
async def test_middlewares():
    async def mock_handler(inputs, ctx, desc):
        return "success"
        
    desc = ToolDescriptor(
        name="test", description="", input_schema={}, output_schema=None,
        timeout_seconds=5.0, max_retries=0, retry_delay_seconds=0, is_idempotent=False,
        required_permissions=frozenset(["read"]), audit_level="NONE", fn=lambda: 1
    )
    ctx = create_anonymous_context("req1", "t1", "s1", datetime.now(UTC))
    
    rl = RateLimitMiddleware(tokens_per_minute=1)
    await rl({}, ctx, desc, mock_handler)
    with pytest.raises(RateLimitError):
        await rl({}, ctx, desc, mock_handler)
        
    sink = LoggerAuditSink()
    audit_mw = AuditMiddleware(sink)
    await audit_mw({"foo": "bar"}, ctx, desc, mock_handler)
    assert len(sink.records) == 1
    assert sink.records[0].outcome == "success"
    assert sink.records[0].action == "tool:call"
    
    async def error_handler(inputs, ctx, desc):
        raise ValueError("fail")
    with pytest.raises(ValueError):
        await audit_mw({}, ctx, desc, error_handler)
    # Auth Middleware
    auth_mw = AuthenticationMiddleware(ApiKeyAuth({"secret-123"}))
    with pytest.raises(Exception):
        await auth_mw({}, ctx, desc, mock_handler)
    ctx_with_key = create_anonymous_context("r", "t", "s", datetime.now(UTC))
    from dataclasses import replace
    ctx_with_key = replace(ctx_with_key, metadata={"api_key": "secret-123"})
    res = await auth_mw({}, ctx_with_key, desc, mock_handler)
    assert res == "success"
    
    # Authorization Middleware
    policy_engine = RBACPolicyEngine({"user": {"read"}})
    authz_mw = AuthorizationMiddleware(policy_engine)
    
    # Context currently has anonymous caller_id with no roles
    with pytest.raises(Exception):
        await authz_mw({}, ctx, desc, mock_handler)
        
    ident_user = Identity("u1", "u", {"roles": ["user"]})
    ctx_authz = replace(ctx, caller_identity=ident_user)
    res = await authz_mw({}, ctx_authz, desc, mock_handler)
    assert res == "success"
