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
pip install aegis-mcp
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

### Multi-Agent Mesh & Runtime

AegisMCP extends the Model Context Protocol far beyond simple remote procedure calls.

#### AegisAgent

The `AegisAgent` class acts as the brains of your system. You provide it a `ModelProvider` (like Anthropic or OpenAI) and a list of tool names. It autonomously iterates through an execution loop, deciding which tools to call.

#### The agent_as_tool Pattern

In a true Enterprise Multi-Agent Mesh, agents need to talk to other agents. AegisMCP allows you to instantly convert an entire `AegisAgent` into a standard MCP tool using the `agent_as_tool` adapter.

This allows a top-level Router Agent to call a "Database Analyst Agent" simply by executing a tool call, seamlessly passing contexts down the tree.

### Security Model

AegisMCP treats security as a first-class citizen using the `ExecutionPipeline` and `Middleware` architecture.

#### Role-Based Access Control (RBAC)

When defining a tool, you can specify `required_permissions`:

```python
@app.tool(required_permissions={"admin:write"})
async def delete_user(user_id: str):
    pass
```

The pipeline verifies the identity attached to the `AegisContext`.

#### API Key Authentication

AegisMCP provides built-in `ApiKeyMiddleware`. It extracts tokens from headers (in HTTP transports) or connection payloads (in WebSockets).

#### Rate Limiting

The `RateLimitMiddleware` ensures that a single identity cannot spam the RPC server, preventing DOS attacks.

### Workflows & Deterministic Sagas

AegisMCP uses the `WorkflowEngine` to implement the **Saga Pattern**.

#### Why Sagas?

In a multi-agent or multi-tool system, tasks often require multiple sequential steps (e.g., Book Flight, Reserve Hotel, Charge Credit Card). 

If "Charge Credit Card" fails, you can't simply throw an error—you must roll back the hotel and flight!

#### Implementation

```python
class BookFlightStep:
    async def execute(self, ctx: AegisContext):
        return await flight_api.book()
        
    async def compensate(self, ctx: AegisContext):
        # Triggered automatically if ANY subsequent step fails!
        await flight_api.cancel()
```

AegisMCP executes these sagas deterministically, ensuring your enterprise system always returns to a stable state.

## Author

**Ujjwal Jagtap** 
* Email: [ujjwaljagtap7@gmail.com](mailto:ujjwaljagtap7@gmail.com)
* GitHub: [Ujje421](https://github.com/Ujje421)

Built with ❤️ for the AI integration community.
