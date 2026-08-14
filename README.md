# AegisMCP 🛡️

AegisMCP is an opinionated, high-performance **Model Context Protocol (MCP)** framework designed for enterprise scale. 

If FastMCP is Flask, AegisMCP is Django. It provides a robust kernel, integrated zero-dependency abstractions, and high-performance asynchronous orchestration to scale your multi-agent architecture.

---

## Why AegisMCP?

- **Parallel Tool Execution:** Native `asyncio.gather` tool orchestrations vastly reduce latency during dense multi-tool generation.
- **AegisContext Everywhere:** Explicit context propagation eliminates race conditions and ties every tool call to standard IDs (`request_id`, `trace_id`, `span_id`).
- **Zero Mandatory Dependencies:** The core framework requires only `pydantic` and `anyio`. Run a basic stdio server in a 50MB container.
- **First-Class Security:** Stop bolting on security. AegisMCP gives you fully customizable Auth, RBAC policy gating, Rate Limiting, and Audit Logging right out of the box.
- **Built-In Agent Runtime:** Scale your AI via hierarchical sub-agents, deterministic Saga workflows, and multi-tool selection logic via the built-in Layer 5/6 engines.

## Installation

```bash
pip install aegismcp
```

Or install with all optional extensions (HTTP transports, observability SDKs, vector database adapters):
```bash
pip install aegismcp[all]
```

## Quick Start (Stdio)

The simplest AegisMCP application runs entirely over Stdio.

```python
import asyncio
from aegismcp.server.app import AegisMCP

app = AegisMCP("HelloWorld")

@app.tool(description="Say hello")
async def say_hello(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    asyncio.run(app.run_stdio())
```

## Enterprise Security (API Keys + RBAC)

```python
import asyncio
from aegismcp.server.app import AegisMCP
from aegismcp.security.auth.apikey import ApiKeyAuth
from aegismcp.security.policy.rbac import RBACPolicyEngine

# Define Identity verification logic
async def verify_key(key: str):
    if key == "secret": return {"id": "user123", "roles": ["admin"]}
    return None

auth = ApiKeyAuth(verify_key)
policy = RBACPolicyEngine(role_permissions={"admin": frozenset(["users:read", "users:write"])})

app = AegisMCP("SecureApp", auth=auth, policy=policy)

@app.tool(
    description="Secure data retrieval",
    required_permissions=frozenset(["users:read"])
)
async def get_secure_data() -> str:
    return "Sensitive Information"
```

## Deterministic Workflows

```python
import asyncio
from aegismcp.server.app import AegisMCP
from aegismcp.kernel.context import AegisContext

app = AegisMCP("WorkflowApp")

class Step1:
    async def execute(self, ctx: AegisContext): return "Step 1"
    async def compensate(self, ctx: AegisContext): print("Rolling back Step 1")

@app.workflow("onboarding")
async def onboarding_saga(ctx: AegisContext):
    # This automatically rolls back on failure in reverse order
    return await app.workflow_engine.execute_saga([
        (Step1(), (), {}),
        # ... Add Step 2 that throws Error
    ], ctx)
```

## Advanced Agent Runtimes
For more advanced integrations (like RAG, Multi-Agent Mesh, or Semantic Tool Selection), view our [architecture decisions](docs/ARCHITECTURE_DECISIONS.md) and [full examples suite](examples/).
