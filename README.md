# AegisMCP

AegisMCP is an opinionated, high-performance Model Context Protocol (MCP) framework designed for enterprise scale. 

## Features

- **AegisContext Everywhere**: Explicit context propagation for robust state management.
- **Parallel Tool Execution**: Substantial latency reductions by parallelizing independent tools.
- **Universal Agent Runtime**: Compatible with any standard MCP server.
- **Zero Mandatory Dependencies**: Core framework requires only `pydantic` and `anyio`. Run a basic stdio server in a 50MB container.
- **First-Class Security**: Built-in RBAC, audit logging, and OPA integration out of the box.

## Installation

```bash
pip install aegismcp
```

## Quick Start (Hello World)

```python
import asyncio
from aegismcp.server.app import AegisMCP

app = AegisMCP("HelloWorld")

@app.tool(description="Say hello")
def say_hello(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    asyncio.run(app.run_stdio())
```
