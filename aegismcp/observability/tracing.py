from typing import Any, Protocol


class Span(Protocol):
    def set_attribute(self, key: str, value: str | int | float | bool) -> None: ...
    def set_status(self, status: str, description: str | None = None) -> None: ...
    def __enter__(self) -> 'Span': ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

class TracerProvider(Protocol):
    def start_span(self, name: str) -> Span: ...

class InMemorySpan(Span):
    def __init__(self, name: str):
        self.name = name
        self.attributes: dict[str, Any] = {}
        self.status: str = "OK"
        self.status_description: str | None = None
        
    def set_attribute(self, key: str, value: str | int | float | bool) -> None:
        self.attributes[key] = value
        
    def set_status(self, status: str, description: str | None = None) -> None:
        self.status = status
        self.status_description = description
        
    def __enter__(self) -> 'Span':
        return self
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.status = "ERROR"
            self.status_description = str(exc_val)

class InMemoryTracerProvider(TracerProvider):
    def __init__(self) -> None:
        self.spans: list[InMemorySpan] = []
        
    def start_span(self, name: str) -> Span:
        span = InMemorySpan(name)
        self.spans.append(span)
        return span
