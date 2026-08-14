# AegisMCP Security Model

AegisMCP treats security as a first-class citizen using the `ExecutionPipeline` and `Middleware` architecture.

## Role-Based Access Control (RBAC)

When defining a tool, you can specify `required_permissions`:

```python
@app.tool(required_permissions={"admin:write"})
async def delete_user(user_id: str):
    pass
```

The pipeline verifies the identity attached to the `AegisContext`.

## API Key Authentication

AegisMCP provides built-in `ApiKeyMiddleware`. It extracts tokens from headers (in HTTP transports) or connection payloads (in WebSockets).

## Rate Limiting

The `RateLimitMiddleware` ensures that a single identity cannot spam the RPC server, preventing DOS attacks.
