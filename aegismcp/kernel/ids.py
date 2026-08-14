import uuid


def generate_request_id() -> str:
    """
    Generate a globally unique request ID.

    The architecture document specifies UUIDv7 by default. To maintain zero mandatory
    dependencies beyond pydantic/anyio, we use UUIDv4 (stdlib) for now.
    """
    return str(uuid.uuid4())


def generate_trace_id() -> str:
    """Generate an OpenTelemetry-compatible trace ID (32 hex chars)."""
    return uuid.uuid4().hex


def generate_span_id() -> str:
    """Generate an OpenTelemetry-compatible span ID (16 hex chars)."""
    return uuid.uuid4().hex[:16]
