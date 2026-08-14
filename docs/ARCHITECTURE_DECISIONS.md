# Architectural Decisions & Progress Log

This document tracks the core implementation decisions and architectural trade-offs for the AegisMCP framework.

## Phase 0: Foundation & Protocol
**Status**: ✅ Complete
- **Zero Dependencies Rule**: Used only standard library + `pydantic` and `anyio`.
- **Robust Protocol Codec**: Built a rigid JSON-RPC 2.0 codec returning strict structural types.

## Phase 1: Execution & Pipelines
**Status**: ✅ Complete
- **Pipeline Architecture**: Adopted an ordered, async middleware pipeline (`ExecutionPipeline`) for extensible security.
- **Strict Deadlines**: Intelligently utilizes `asyncio.wait_for` enforcing timeouts tied to `AegisContext`.

## Phase 2: Client & Transports
**Status**: ✅ Complete
- **Transport Interfaces**: Created generic `Transport` base classes with `StdioTransport` and `WebSocketTransport`.
- **AegisClient**: Built a fully asynchronous client to consume external MCP servers dynamically.

## Phase 3: Enterprise Security 
**Status**: ✅ Complete
- **Middleware Integration**: Implemented `AuthenticationMiddleware`, `RateLimitMiddleware`, and `AuditMiddleware`.
- **RBAC Policy**: Created role-based access control where Tools declare `required_permissions`. The pipeline blocks execution before tool invocation if the token lacks permissions.

## Phase 4: Observability
**Status**: ✅ Complete
- **Distributed Tracing**: `AegisContext` acts as the carrier for `trace_id` and `span_id`.
- **Metrics**: Standardized interface for `counter` and `histogram` logic during executions.

## Phase 5: Fast Application Server
**Status**: ✅ Complete
- **AegisMCP App Object**: Modeled after FastAPI/Flask to provide a user-friendly interface (`@app.tool`).
- **Dependency Injection**: Seamlessly wires together Transports, Codecs, and Pipelines under the hood.

## Phase 6: Advanced Agent Runtime & Mesh
**Status**: ✅ Complete
- **AegisAgent Engine**: Added LLM `ModelProvider` protocol. Agents can automatically invoke their own tool lists recursively.
- **agent_as_tool (Sub-Agent Mesh)**: Allowed agents to dynamically wrap other agents as standard MCP tools, forming hierarchical "Agent Meshes".
- **Saga Pattern (Workflows)**: Implemented `WorkflowEngine` to support compensating transactions. If step 4 of a 5-step flow fails, the engine automatically rolls back steps 3, 2, and 1.

## Phase 7: Production Hardening
**Status**: ✅ Complete
- **Hatchling Packaging**: Modern `pyproject.toml` distribution.
- **100% Type Coverage**: Strict `mypy` enforcement.
