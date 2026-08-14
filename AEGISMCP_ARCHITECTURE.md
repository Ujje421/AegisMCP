# AegisMCP — Master Architecture Document
> **Version:** 0.1-arch  
> **Status:** Foundation design — pre-implementation  
> **Author:** Principal Architecture Review  

---

## 0. Why this document exists

Every great framework has one moment where it diverged from being "another library" and became something developers build careers around. FastMCP is a great *wrapper*. LangChain is a great *experiment*. Neither is a great *framework*.

AegisMCP is designed to be the framework — the one Python developers reach for when the stakes are real.

This document makes every significant architectural decision explicit, explains the *why* behind it, and defines the contracts between layers. A new contributor should be able to read this and understand not just what the code does, but why it was built that way.

---

## 1. Core thesis: what makes a framework win

Frameworks win on **three axes**, in this order of importance:

1. **Correctness** — it does what the spec says, every time, with no edge-case surprises.
2. **Developer experience** — the 5-minute path is obvious; the 5-hour path is not frustrating.
3. **Production readiness** — observability, security, and failure modes are first-class, not afterthoughts.

AegisMCP's competitors fail differently:

| Framework | How it fails |
|---|---|
| FastMCP | Excellent DX, thin production story, no agent runtime |
| LangChain | Too much magic, poor error messages, circular abstractions |
| LlamaIndex | Strong RAG, weak MCP integration, complex config surface |
| Official MCP SDK | Correct protocol, no opinions, full assembly required |

AegisMCP wins by being **correct + opinionated + observable** from day one.

---

## 2. The kernel concept

Every layer in AegisMCP composes from a single primitive: **`AegisContext`**.

```python
@dataclass(frozen=True)
class AegisContext:
    request_id: str               # globally unique, propagated across all tool calls
    trace_id: str                 # OpenTelemetry-compatible
    span_id: str
    caller_identity: Identity     # who is making this request
    permissions: FrozenSet[str]   # resolved at request boundary, never re-evaluated mid-chain
    deadline: datetime            # hard timeout, propagated to every sub-call
    metadata: FrozenMapping       # arbitrary KV, passed through without modification
    baggage: FrozenMapping        # OTel baggage
```

This is not a global. It is not a thread-local. It is a value passed explicitly through every boundary.

**Why this matters:**

- Zero hidden state. Every function that touches a request takes `ctx: AegisContext`.
- Tracing is free: span_id is already there.
- Security is enforced: permissions are resolved once at the boundary and frozen.
- Deadlines compose: `ctx.with_deadline(ctx.deadline - timedelta(seconds=1))` naturally narrows timeouts.
- Testing is simple: construct an `AegisContext` with any values you want.

This is the design decision that separates a framework from a library. A library lets you put state wherever you want. A framework decides where state lives, and AegisMCP decides: inside a frozen, propagated context object.

---

## 3. Architecture layers

```
Layer 8  ── Deployment & Config
Layer 7  ── Developer Surface  (@tool, CLI, testing)
Layer 6  ── Transport          (stdio, HTTP, WebSocket, gRPC)
Layer 5  ── Agent Runtime      (planner, memory, RAG, workflow, multi-agent)
Layer 4A ── Security           (AuthN, RBAC, policy engine)
Layer 4B ── Observability      (OTel, metrics, cost)
Layer 3A ── MCP Server         (handler, capability advertiser)
Layer 3B ── MCP Client         (discovery, invocation, pool)
Layer 2  ── Execution Engine   (executor, pipeline, concurrency)
Layer 1  ── MCP Protocol       (codec, negotiation, lifecycle FSM)
Layer 0  ── Kernel             (AegisContext, event bus, type system, errors)
```

**Rule:** upper layers may use lower layers; lower layers must never import upper layers. This is enforced by the package structure and verified by CI import-graph checks.

---

## 4. Layer 0: Kernel

### 4.1 Package: `aegismcp.kernel`

This package has **zero external runtime dependencies**. It is the one thing that must never break.

```
aegismcp/kernel/
    context.py        # AegisContext, Identity, FrozenMapping
    errors.py         # exception hierarchy
    events.py         # internal event bus (publish/subscribe, async)
    types.py          # core type aliases: ToolName, ResourceURI, PermissionSet
    clock.py          # injectable clock (real + fake for testing)
    ids.py            # request_id / trace_id generation (UUIDv7 by default)
```

### 4.2 Exception hierarchy

```
AegisError                        # base; always has request_id, timestamp, is_retryable
├── ProtocolError                 # MCP spec violation
│   ├── InvalidMessageError
│   ├── UnsupportedCapabilityError
│   └── VersionMismatchError
├── ExecutionError                # tool/resource execution failures
│   ├── ToolNotFoundError
│   ├── ToolTimeoutError
│   ├── ToolRetryExhaustedError
│   └── ResourceNotFoundError
├── SecurityError                 # auth/authz failures (never leaks internals)
│   ├── AuthenticationError
│   ├── AuthorizationError
│   └── PolicyViolationError
├── ValidationError               # schema/input failures
│   └── SchemaValidationError
├── TransportError
│   ├── ConnectionError
│   └── SerializationError
└── ConfigurationError
```

**Rules for all exceptions:**
- Always include `request_id` if one is in scope.
- `is_retryable: bool` — the executor uses this; callers should not guess.
- Never include secrets, stack traces, or internal paths in the message string.
- The `__str__` output must be safe to log at any level.

### 4.3 Internal event bus

Used only for decoupled internal communication (e.g., the executor publishing a `ToolExecuted` event that the observability layer subscribes to). **Not exposed to framework users.**

```python
# Internal use only — not part of the public API
bus = EventBus()
bus.subscribe(ToolExecuted, metrics_handler)
bus.subscribe(ToolExecuted, audit_handler)

await bus.publish(ToolExecuted(ctx=ctx, tool_name="get_customer", duration_ms=12))
```

This decouples observability and security audit from execution logic without adding function parameters.

---

## 5. Layer 1: MCP Protocol

### 5.1 Design decision: own the codec

AegisMCP does not depend on the official MCP Python SDK at the protocol layer. Instead, it implements the codec itself from the MCP specification.

**Why:** The official SDK is a reference implementation. It will change as the spec evolves. AegisMCP needs to control protocol versioning, add instrumentation hooks, and potentially support multiple spec versions simultaneously. Depending on an external SDK at the lowest layer removes that control.

**What we do instead:** Read the spec. Implement a typed codec. Test against the spec's example messages. Validate interoperability with the official SDK in integration tests.

### 5.2 Lifecycle FSM

Every MCP session is a finite state machine:

```
CONNECTING → NEGOTIATING → READY → EXECUTING → CLOSING → CLOSED
                                        ↑___________↓
                                     (tool calls cycle here)
```

The FSM is implemented as an explicit class, not implicit state spread across methods. State transitions emit events on the internal bus.

### 5.3 Version shim

```python
class ProtocolVersionShim:
    def translate_v1_to_v2(self, message: RawMessage) -> RawMessage: ...
    def translate_v2_to_v1(self, message: RawMessage) -> RawMessage: ...
```

When MCP evolves, AegisMCP can support both old and new clients without rewriting the execution layer.

---

## 6. Layer 2: Execution Engine

### 6.1 The middleware pipeline

This is where most framework power lives. Every request passes through a pipeline of handlers:

```
InboundRequest
      │
      ▼
[DeadlineMiddleware]      ── sets ctx.deadline, starts the clock
      │
      ▼
[AuthenticationMiddleware] ── resolves identity → ctx.caller_identity
      │
      ▼
[AuthorizationMiddleware]  ── checks permissions → ctx.permissions (frozen)
      │
      ▼
[RateLimitMiddleware]      ── token bucket per identity
      │
      ▼
[ValidationMiddleware]     ── schema validation against tool's Pydantic model
      │
      ▼
[TracingMiddleware]        ── opens OTel span
      │
      ▼
[ToolExecutor]            ── calls the actual Python function
      │
      ▼
[OutputValidationMiddleware] ── validates output schema
      │
      ▼
[AuditMiddleware]          ── appends immutable audit record
      │
      ▼
OutboundResponse
```

Middleware is composable. Framework users can inject custom middleware:

```python
app = AegisMCP("My Service")
app.add_middleware(MyCustomMiddleware)
```

The order of built-in middleware is non-negotiable. User middleware inserts between OutputValidation and Audit by default (configurable).

### 6.2 The concurrency governor

```python
class ConcurrencyGovernor:
    max_concurrent_tools: int        # global cap
    per_tool_semaphores: dict        # per-tool cap
    per_identity_semaphores: dict    # per-user cap
    queue_depth: int                 # max waiting requests before rejection
```

This prevents a burst of requests from starving the event loop. No framework-level backpressure = production incidents.

### 6.3 Tool execution contract

Every tool registration produces a `ToolDescriptor`:

```python
@dataclass
class ToolDescriptor:
    name: str
    description: str
    input_schema: JsonSchema         # derived from Pydantic model or type hints
    output_schema: JsonSchema | None
    timeout_seconds: float
    max_retries: int
    retry_delay_seconds: float
    is_idempotent: bool              # allows safe retry on network failure
    required_permissions: FrozenSet[str]
    audit_level: AuditLevel          # NONE | METADATA | FULL
    fn: Callable
```

The descriptor is generated at import time (not at request time). This means schema errors are caught at startup, not in production.

---

## 7. Layers 3A/3B: Server and Client

### 7.1 The app object

```python
from aegismcp import AegisMCP

app = AegisMCP(
    name="Customer Service",
    version="1.0.0",
    description="Handles customer queries",
    auth=ApiKeyAuth(keys=from_env("API_KEYS")),
    config=AegisConfig.from_env(),
)

@app.tool(
    description="Retrieve a customer by ID",
    timeout=10.0,
    permissions={"customer:read"},
    audit=AuditLevel.METADATA,
)
async def get_customer(customer_id: Annotated[str, "UUID of the customer"]) -> Customer:
    ...
```

### 7.2 The client

```python
from aegismcp import AegisClient

async with AegisClient.connect("stdio://./my_server.py") as client:
    tools = await client.list_tools()
    result = await client.call_tool("get_customer", {"customer_id": "123"})
    customer = result.as_model(Customer)   # typed extraction
```

The client uses the same `AegisContext` propagation as the server. A trace that starts on the client spans into server execution transparently.

---

## 8. Layer 4A: Security

### 8.1 Design principle: secure by default

An `AegisMCP` app with no security config rejects all requests except from `localhost`. This is wrong in a demo but right in production. The developer must explicitly configure auth — it cannot be accidentally forgotten.

### 8.2 Authentication strategies

```python
class AuthStrategy(Protocol):
    async def authenticate(self, request: RawRequest) -> Identity | None: ...

# Built-in implementations:
ApiKeyAuth        # header-based API key
JWTAuth           # RS256/ES256 JWT validation
OAuth2Auth        # PKCE + token introspection
mTLSAuth          # mutual TLS client certificate
CompositeAuth     # try multiple strategies in order
```

### 8.3 Authorization: policy engine

Permissions are not hardcoded strings. They are evaluated by a policy engine:

```python
class PolicyEngine(Protocol):
    async def evaluate(
        self,
        identity: Identity,
        action: str,          # e.g., "tool:call"
        resource: str,        # e.g., "tool:get_customer"
        ctx: AegisContext,
    ) -> PolicyDecision: ...   # ALLOW | DENY | DENY_WITH_REASON

# Built-in implementations:
RBACPolicyEngine          # role → permission set
AttributePolicyEngine     # ABAC (identity attributes × resource attributes)
OPAPolicyEngine           # delegates to Open Policy Agent
```

### 8.4 Audit log

Audit records are **immutable and append-only**. They are written to a separate sink from application logs:

```python
@dataclass(frozen=True)
class AuditRecord:
    request_id: str
    timestamp: datetime
    caller_id: str
    action: str               # "tool:call", "resource:read", etc.
    resource: str
    decision: PolicyDecision
    inputs_hash: str | None   # SHA-256 of inputs (not the inputs themselves)
    outcome: str              # "success" | "error" | "timeout"
    duration_ms: float
```

The inputs are hashed, not stored. This satisfies audit requirements without storing sensitive data in the audit log.

---

## 9. Layer 4B: Observability

### 9.1 OpenTelemetry as the spine

AegisMCP emits OpenTelemetry signals natively. No vendor SDK required. Users configure their own exporter.

```python
app = AegisMCP(
    "My Service",
    telemetry=OTelConfig(
        service_name="customer-service",
        exporter=OTLPGrpcExporter(endpoint="localhost:4317"),
    )
)
```

### 9.2 Automatic instrumentation

Every tool call automatically produces:

- **Trace span:** `aegismcp.tool.{tool_name}` with standard attributes
- **Metric:** `aegismcp.tool.calls` (counter, labels: tool_name, outcome, identity)
- **Metric:** `aegismcp.tool.duration` (histogram, p50/p95/p99)
- **Metric:** `aegismcp.tool.errors` (counter, labels: error_type)

### 9.3 Cost tracking

For agent runtime (Layer 5), token usage from model calls is tracked:

```python
@dataclass
class ModelCallRecord:
    request_id: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None   # None if pricing unknown
```

This accumulates per-request and per-session, making cost attribution to callers trivial.

---

## 10. Layer 5: Agent Runtime

### 10.1 The critical design decision

The agent runtime is **not** a wrapper around the MCP server. It is a peer component that *uses* the MCP client.

```
User request
     │
     ▼
AegisAgent (Layer 5)
     │
     ├── ModelProvider.generate()        # LLM call
     │
     ├── ToolSelector.select()           # pick tools from registry
     │
     └── AegisClient.call_tool()         # execute tool via MCP (Layer 3B)
            │
            ▼
         AegisMCP Server (Layer 3A)
            │
            ▼
         Tool function (your Python code)
```

This means the agent runtime can connect to *any* MCP server, not just AegisMCP ones. It is interoperable by design.

### 10.2 Model provider interface

```python
class ModelProvider(Protocol):
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDescriptor],
        config: GenerationConfig,
        ctx: AegisContext,
    ) -> ModelResponse: ...

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDescriptor],
        config: GenerationConfig,
        ctx: AegisContext,
    ) -> AsyncIterator[ModelResponseChunk]: ...
```

Built-in adapters: `AnthropicProvider`, `OpenAIProvider`, `GeminiProvider`, `OllamaProvider`.

**Key design:** the interface normalizes tool calling formats. Anthropic, OpenAI, and Gemini all have different tool-call schemas. The adapter translates. The agent runtime never knows which vendor it is using.

### 10.3 The agent loop

```python
class AegisAgent:
    async def run(self, user_message: str, ctx: AegisContext) -> AgentResult:
        messages = [Message.user(user_message)]
        max_turns = self.config.max_turns   # hard cap prevents infinite loops

        for turn in range(max_turns):
            # 1. Select relevant tools (not all of them)
            relevant_tools = await self.tool_selector.select(messages, self.tool_registry)

            # 2. Generate model response
            response = await self.model.generate(messages, relevant_tools, ctx=ctx)

            # 3. If no tool calls, we have the final answer
            if not response.tool_calls:
                return AgentResult(content=response.content, turns=turn + 1)

            # 4. Execute tool calls (potentially in parallel if independent)
            tool_results = await asyncio.gather(*[
                self.client.call_tool(tc.name, tc.arguments, ctx=ctx)
                for tc in response.tool_calls
            ])

            # 5. Append to message history and loop
            messages.append(response.as_assistant_message())
            messages.extend([tr.as_tool_message() for tr in tool_results])

        raise AgentError("Max turns exceeded", is_retryable=False)
```

Notable: step 4 runs independent tool calls in parallel. This is a significant latency win that most frameworks miss.

### 10.4 Tool selector (the key differentiator)

For large tool registries (100+ tools), sending all tool descriptors to the model is expensive and noisy. The tool selector addresses this:

```python
class ToolSelector(Protocol):
    async def select(
        self,
        messages: list[Message],
        registry: ToolRegistry,
        max_tools: int = 20,
    ) -> list[ToolDescriptor]: ...

# Built-in implementations:
AllToolsSelector           # sends everything (fine for < 20 tools)
SemanticToolSelector       # embedding similarity against message history
KeywordToolSelector        # BM25 keyword match (no embeddings needed)
HybridToolSelector         # semantic + keyword with RRF fusion
```

This is the feature that makes AegisMCP scale to enterprise tool registries.

### 10.5 Memory

```python
class Memory(Protocol):
    async def store(self, key: str, value: Any, ctx: AegisContext) -> None: ...
    async def retrieve(self, key: str, ctx: AegisContext) -> Any | None: ...
    async def search(self, query: str, ctx: AegisContext, k: int = 5) -> list[MemoryItem]: ...

# Built-in implementations:
InMemoryMemory             # ephemeral, per-session
RedisMemory               # persistent, TTL-based
PgVectorMemory            # PostgreSQL + pgvector for semantic search
ChromaMemory              # Chroma vector database
```

### 10.6 Workflow engine

Deterministic workflows are separate from probabilistic agent reasoning. Never conflate them.

```python
@app.workflow
class CustomerOnboarding:
    async def run(self, customer_id: str, ctx: AegisContext):
        customer = await self.steps.validate_customer(customer_id, ctx=ctx)
        account  = await self.steps.create_account(customer, ctx=ctx)
        await asyncio.gather(
            self.steps.send_welcome_email(account, ctx=ctx),
            self.steps.provision_access(account, ctx=ctx),
        )
        return account

    async def compensate(self, customer_id: str, ctx: AegisContext):
        # Saga compensation: undo in reverse order
        ...
```

Workflows support: sequential, parallel, branching, saga compensation, human approval gates, retries with backoff, and checkpointing for long-running workflows.

---

## 11. Layer 6: Transport

### 11.1 Transport interface

```python
class Transport(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def receive(self) -> AsyncIterator[RawMessage]: ...
    async def send(self, message: RawMessage) -> None: ...
```

Built-in: `StdioTransport`, `HTTPTransport` (HTTP + SSE), `WebSocketTransport`.

The execution engine never knows which transport is in use. This enables the same server to serve stdio for local Claude desktop integration and HTTP for production API usage simultaneously.

---

## 12. Layer 7: Developer Surface

### 12.1 The @tool decorator — full specification

```python
@app.tool(
    name="get_customer",                    # optional — defaults to function name
    description="Retrieve a customer",      # required
    timeout=10.0,                           # seconds (default: 30.0)
    max_retries=3,                          # on retryable errors (default: 0)
    retry_delay=1.0,                        # seconds between retries
    is_idempotent=True,                     # safe to retry on network failure
    permissions={"customer:read"},          # required permissions
    rate_limit="100/minute",               # per-identity rate limit
    audit=AuditLevel.METADATA,             # NONE | METADATA | FULL
    cache_ttl=60,                          # seconds (None = no caching)
    tags=["customer", "read"],             # for tool discovery
)
async def get_customer(
    customer_id: Annotated[str, Field(description="UUID of the customer")],
    include_orders: bool = False,
) -> Customer:
    ...
```

Every parameter has a sensible default. The simplest usage is:

```python
@app.tool(description="Get a customer")
async def get_customer(customer_id: str) -> Customer:
    ...
```

### 12.2 Type-driven schema generation

Input schemas are derived from Python type annotations using Pydantic. No separate schema definition is required. Supported types:

- All Python primitives: `str`, `int`, `float`, `bool`
- `Annotated[T, Field(...)]` for descriptions, constraints, examples
- `Pydantic BaseModel` for complex inputs
- `list[T]`, `dict[str, T]`, `Optional[T]`, `Union[T, U]`
- `Literal["a", "b"]` for enumerated values
- `Enum` subclasses

### 12.3 CLI

```
aegis init              # scaffold a new project
aegis dev               # run with hot reload + debug UI
aegis run               # production run
aegis inspect           # connect to a running server, explore tools/resources
aegis tools list        # list registered tools
aegis tools call <name> # call a tool interactively
aegis test              # run the test suite
aegis bench             # run performance benchmarks
aegis doctor            # verify environment, config, and connectivity
```

### 12.4 Testing utilities

```python
from aegismcp.testing import AegisMCPTestClient, mock_tool, assert_tool_called

async def test_customer_lookup():
    async with AegisMCPTestClient(app) as client:
        result = await client.call_tool("get_customer", {"customer_id": "123"})
        assert result.output["name"] == "Alice"

async def test_agent_selects_correct_tool():
    agent = AegisAgent(app, model=MockModelProvider(
        responses=[
            ModelResponse(tool_calls=[ToolCall("get_customer", {"customer_id": "123"})])
        ]
    ))
    result = await agent.run("Who is customer 123?")
    assert result.turns == 1
```

---

## 13. Critical design decisions (with alternatives considered)

### 13.1 Immutable AegisContext vs. thread-local / contextvars

**Decision:** Immutable frozen dataclass passed explicitly.

**Alternatives considered:**
- `contextvars.ContextVar` (Python's built-in) — loses the value across process boundaries, hard to inspect in tests, implicit coupling.
- Thread-local — breaks under async, disaster in an async-first framework.
- Global request object (Flask style) — magic, implicit, impossible to test.

**Why the explicit approach wins:** Every function that touches a request becomes trivially testable by constructing an `AegisContext` directly. No mocking infrastructure needed.

### 13.2 Own codec vs. depend on official SDK

**Decision:** Own the codec.

**Why:** Dependency on official SDK at Layer 1 means the official SDK's release cycle controls our release cycle. When MCP 2.0 ships, we need to support both 1.x and 2.x servers simultaneously. A version shim inside our codec enables this; depending on an external SDK does not.

### 13.3 Middleware pipeline vs. hooks/signals

**Decision:** Explicit ordered middleware pipeline.

**Why:** Hooks and signals (Django-style) are flexible but non-deterministic in ordering. The security middleware MUST run before the executor. The tracing middleware MUST wrap the executor. An explicit ordered pipeline makes this guarantee enforceable by the type system.

### 13.4 Agent runtime as client user vs. tightly coupled to server

**Decision:** Agent runtime uses the MCP client, not the server directly.

**Why:** This means the agent can connect to non-AegisMCP servers (including Anthropic's own, any future third-party). The agent runtime becomes a universal runtime, not an AegisMCP-only component. This is a significant competitive advantage.

### 13.5 Parallel tool execution in the agent loop

**Decision:** Independent tool calls run in parallel via `asyncio.gather`.

**Why:** Most agent frameworks serialize tool calls. If the model requests `get_customer("123")` and `get_orders("123")` simultaneously, there is no reason to wait for the first before starting the second. On typical API latencies (50–200ms per tool), parallelism halves agent turn time.

**Risk:** Tools with side effects should not be parallelized. We detect this using the `is_idempotent` flag on `ToolDescriptor` — if any tool in a batch is non-idempotent, the batch executes sequentially.

---

## 14. Repository structure

```
aegismcp/
│
├── aegismcp/
│   ├── kernel/
│   │   ├── __init__.py
│   │   ├── context.py           # AegisContext, Identity
│   │   ├── errors.py            # full exception hierarchy
│   │   ├── events.py            # internal event bus
│   │   ├── types.py             # ToolName, ResourceURI, etc.
│   │   ├── clock.py             # injectable clock
│   │   └── ids.py               # request/trace ID generation
│   │
│   ├── protocol/
│   │   ├── __init__.py
│   │   ├── codec.py             # MCP message encode/decode
│   │   ├── messages.py          # typed MCP message models
│   │   ├── lifecycle.py         # session FSM
│   │   ├── negotiation.py       # capability negotiation
│   │   └── versioning.py        # version shim
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── pipeline.py          # middleware pipeline
│   │   ├── executor.py          # tool/resource/prompt execution
│   │   ├── concurrency.py       # governor, semaphores
│   │   ├── retry.py             # retry logic with backoff
│   │   └── middleware/
│   │       ├── deadline.py
│   │       ├── auth.py
│   │       ├── ratelimit.py
│   │       ├── validation.py
│   │       ├── tracing.py
│   │       └── audit.py
│   │
│   ├── server/
│   │   ├── __init__.py
│   │   ├── app.py               # AegisMCP app object
│   │   ├── handler.py           # request dispatch
│   │   └── capabilities.py      # capability advertisement
│   │
│   ├── client/
│   │   ├── __init__.py
│   │   ├── client.py            # AegisClient
│   │   ├── pool.py              # connection pool
│   │   └── discovery.py         # tool/resource discovery
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── decorator.py         # @tool, @app.tool
│   │   ├── descriptor.py        # ToolDescriptor
│   │   ├── registry.py          # ToolRegistry
│   │   └── schema.py            # type → JSON schema
│   │
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── decorator.py
│   │   ├── descriptor.py
│   │   └── registry.py
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── decorator.py
│   │   ├── descriptor.py
│   │   └── registry.py
│   │
│   ├── transports/
│   │   ├── __init__.py
│   │   ├── base.py              # Transport protocol
│   │   ├── stdio.py
│   │   ├── http.py              # HTTP + SSE
│   │   └── websocket.py
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── base.py
│   │   │   ├── apikey.py
│   │   │   ├── jwt.py
│   │   │   ├── oauth2.py
│   │   │   └── mtls.py
│   │   ├── policy/
│   │   │   ├── base.py
│   │   │   ├── rbac.py
│   │   │   ├── abac.py
│   │   │   └── opa.py
│   │   └── audit.py
│   │
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── telemetry.py         # OTel setup
│   │   ├── metrics.py           # metric definitions
│   │   ├── tracing.py           # span helpers
│   │   └── cost.py              # model cost tracking
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py             # AegisAgent
│   │   ├── loop.py              # agent execution loop
│   │   ├── selector.py          # tool selector implementations
│   │   ├── memory/
│   │   │   ├── base.py
│   │   │   ├── inmemory.py
│   │   │   ├── redis.py
│   │   │   └── pgvector.py
│   │   ├── rag/
│   │   │   ├── base.py
│   │   │   ├── chunker.py
│   │   │   ├── embedder.py
│   │   │   └── retriever.py
│   │   └── providers/
│   │       ├── base.py          # ModelProvider protocol
│   │       ├── anthropic.py
│   │       ├── openai.py
│   │       ├── gemini.py
│   │       └── ollama.py
│   │
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── decorator.py
│   │   └── saga.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── models.py            # AegisConfig (Pydantic Settings)
│   │   └── loader.py            # env + YAML loader
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py              # Click app
│   │   └── commands/
│   │       ├── init.py
│   │       ├── dev.py
│   │       ├── run.py
│   │       ├── inspect.py
│   │       └── doctor.py
│   │
│   └── testing/
│       ├── __init__.py
│       ├── client.py            # AegisMCPTestClient
│       ├── mocks.py             # MockModelProvider, mock_tool
│       └── assertions.py        # assert_tool_called, etc.
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── protocol/                # spec conformance tests
│   ├── security/
│   └── performance/
│
├── examples/
│   ├── 01_hello_world/
│   ├── 02_basic_tool/
│   ├── 03_multiple_tools/
│   ├── 04_resources/
│   ├── 05_client/
│   ├── 06_middleware/
│   ├── 07_authentication/
│   ├── 08_agent/
│   ├── 09_rag/
│   ├── 10_workflow/
│   ├── 11_multi_agent/
│   └── 12_production/
│
├── docs/
├── pyproject.toml
├── README.md
├── ARCHITECTURE.md              # (this document, condensed)
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
└── ROADMAP.md
```

---

## 15. Build tooling and quality

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "aegismcp"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.6",
    "anyio>=4.3",
    "click>=8.1",
]

[project.optional-dependencies]
http       = ["httpx>=0.27", "starlette>=0.37", "uvicorn>=0.29"]
observability = ["opentelemetry-sdk>=1.24", "opentelemetry-exporter-otlp>=1.24"]
jwt        = ["python-jose[cryptography]>=3.3"]
redis      = ["redis>=5.0"]
pgvector   = ["asyncpg>=0.29", "pgvector>=0.2"]
agents     = ["anthropic>=0.25", "openai>=1.30", "tiktoken>=0.7"]
all        = ["aegismcp[http,observability,jwt,redis,agents]"]
```

**Zero mandatory dependencies beyond pydantic and anyio.** Every production feature is opt-in. A simple stdio tool server can be deployed in a 50MB container with no cloud SDKs, no databases, no LLM libraries.

**CI pipeline (GitHub Actions):**
- `ruff check` — linting
- `ruff format --check` — formatting
- `mypy --strict` — type checking
- `pytest` — unit + integration
- `pytest tests/protocol/` — spec conformance
- `import-graph-check` — no circular imports, no upper-layer imports in lower layers
- `safety check` — dependency vulnerability scan
- `pip-audit` — CVE scan

---

## 16. Implementation phasing

### Phase 0 (week 1–2): Foundation
- Repository structure
- CI pipeline
- `aegismcp.kernel` complete with 100% test coverage
- `aegismcp.protocol` codec with spec conformance tests

### Phase 1 (week 3–4): Execution + basic server
- Middleware pipeline (without security or observability middleware)
- Tool registration and schema generation
- `AegisMCP` app object
- stdio transport
- Working "hello world" example

### Phase 2 (week 5–6): Client + complete transports
- `AegisClient`
- HTTP transport
- WebSocket transport
- Connection pooling
- Full protocol lifecycle

### Phase 3 (week 7–8): Security
- All auth strategies
- RBAC policy engine
- Audit log
- Rate limiting

### Phase 4 (week 9–10): Observability
- OTel integration
- Metrics
- Cost tracking
- `aegis doctor` and `aegis inspect` CLI commands

### Phase 5 (week 11–14): Agent runtime
- Model provider interface + Anthropic + OpenAI adapters
- Basic agent loop
- Tool selector (semantic)
- Memory (in-memory + Redis)

### Phase 6 (week 15–18): Agent advanced
- RAG pipeline
- Workflow engine
- Multi-agent mesh
- Full example suite

### Phase 7 (week 19–22): Production hardening
- Performance benchmarks
- Load testing
- Security penetration testing
- Documentation complete
- PyPI publish

---

## 17. The moat

Features can be copied. Architecture decisions are sticky.

AegisMCP's architectural moat is:

1. **`AegisContext` everywhere** — once developers build on explicit context propagation, switching to a framework that uses global state feels wrong. Testing is harder. Debugging is harder. They stay.

2. **Parallel tool execution** — this is a measurable latency win. Benchmarks will show it. "AegisMCP agents are 2x faster because they parallelize independent tools" is a repeatable, defensible claim.

3. **Agent runtime + any MCP server** — because the agent uses the MCP client, it works with every MCP server on the planet. This makes AegisMCP the runtime layer for the entire MCP ecosystem, not just its own servers.

4. **Zero mandatory dependencies** — a simple server that runs in a 50MB container is 10x easier to deploy than one that requires a vector database and three cloud SDKs. This matters enormously for enterprise adoption.

5. **Security as a first-class layer** — enterprise teams will pay for a framework that has RBAC, audit logs, and OPA integration built in. Nobody wants to bolt those on after the fact.

---

*End of master architecture document.*
*Next step: implement Phase 0. Start with `aegismcp/kernel/context.py`.*
