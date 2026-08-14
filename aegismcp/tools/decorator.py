from collections.abc import Callable

from .descriptor import ToolDescriptor
from .schema import generate_json_schema


def tool(
    name: str | None = None,
    description: str | None = None,
    timeout: float = 30.0,
    max_retries: int = 0,
    retry_delay: float = 1.0,
    is_idempotent: bool = False,
    permissions: frozenset = frozenset(),
    audit: str = "METADATA",
    cache_ttl: int | None = None,
    tags: list[str] | None = None,
) -> Callable:
    """Decorator to register a function as an MCP tool."""

    def decorator(fn: Callable) -> Callable:
        fn_name = name or fn.__name__
        fn_desc = description or fn.__doc__ or ""

        input_schema = generate_json_schema(fn)

        descriptor = ToolDescriptor(
            name=fn_name,
            description=fn_desc,
            input_schema=input_schema,
            output_schema=None,  # Simplified for now
            timeout_seconds=timeout,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay,
            is_idempotent=is_idempotent,
            required_permissions=permissions,
            audit_level=audit,
            fn=fn,
        )

        # Attach descriptor to the function so it can be picked up by the app registry
        setattr(fn, "__aegis_tool__", descriptor)
        return fn

    return decorator
