# Architectural Decisions & Progress Log

This document tracks the ongoing implementation decisions, progress, and architectural trade-offs for the AegisMCP framework.

## Phase 0: Foundation & Protocol
**Status**: ✅ Complete

**Key Decisions:**
- **Zero Dependencies Rule**: We strictly used standard library modules (`uuid` via `uuid4` as a placeholder for UUIDv7, `datetime` for clock handling) in the core to avoid bloated dependency trees. The only dependencies are `pydantic` and `anyio`.
- **Strict Quality Enforcement**: Enforced `mypy --strict` and `ruff` checks. Attained 100% test coverage on `aegismcp/kernel` and `aegismcp/protocol`.
- **Robust Protocol Codec**: Built a rigid JSON-RPC 2.0 codec using Pydantic models for validation, returning explicit structural types (`JSONRPCRequest`, `JSONRPCResponse`, `JSONRPCError`, `JSONRPCNotification`).

## Phase 1: Execution & Basic Server
**Status**: ✅ Complete

**Key Decisions:**
- **Pipeline Architecture**: Adopted an ordered, async middleware pipeline pattern (`ExecutionPipeline`). This ensures that future layers like security and observability can wrap tool execution seamlessly without altering business logic.
- **Strict Deadlines & Timeouts**: The `ToolExecutor` calculates precise remaining time against the `AegisContext` strict deadline. It intelligently utilizes `asyncio.wait_for()` (for async tools) or `run_in_executor` (for sync tools) to strictly enforce timeouts.
- **Reflective Schema Generation**: Developed an automated JSON Schema generator powered directly by Python's `inspect` and Pydantic's `TypeAdapter`. This allows developers to use standard Python type hints without writing raw JSON schemas manually, vastly improving developer experience.

## Phase 2: Client & Transports
**Status**: ⏳ Planning

**Goals:**
- Implement `AegisClient` for connecting to generic MCP servers.
- Build HTTP (SSE) and WebSocket transports as opt-in dependencies.
- Implement connection pooling for high-concurrency environments.
