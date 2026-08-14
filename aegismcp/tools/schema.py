import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

from pydantic import TypeAdapter


def generate_json_schema(fn: Callable[..., Any]) -> dict[str, Any]:
    """Generate a JSON schema from a function's type hints."""
    sig = inspect.signature(fn)
    hints = get_type_hints(fn, include_extras=True)

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name in hints:
            adapter = TypeAdapter(hints[name])
            properties[name] = adapter.json_schema()
        else:
            properties[name] = {"type": "string"}  # Default fallback

        if param.default == inspect.Parameter.empty:
            required.append(name)

    return {"type": "object", "properties": properties, "required": required}
