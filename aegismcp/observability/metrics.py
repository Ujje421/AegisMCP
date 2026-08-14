from typing import Protocol


class MetricCounter(Protocol):
    def add(self, value: int | float, attributes: dict[str, str] | None = None) -> None: ...


class MetricHistogram(Protocol):
    def record(self, value: int | float, attributes: dict[str, str] | None = None) -> None: ...


class MetricsProvider(Protocol):
    def create_counter(self, name: str, description: str = "") -> MetricCounter: ...
    def create_histogram(self, name: str, description: str = "") -> MetricHistogram: ...


class InMemoryCounter(MetricCounter):
    def __init__(self, name: str):
        self.name = name
        self.value: float = 0.0
        self.records: list[tuple[float, dict[str, str] | None]] = []

    def add(self, value: int | float, attributes: dict[str, str] | None = None) -> None:
        self.value += float(value)
        self.records.append((float(value), attributes))


class InMemoryHistogram(MetricHistogram):
    def __init__(self, name: str):
        self.name = name
        self.records: list[tuple[float, dict[str, str] | None]] = []

    def record(self, value: int | float, attributes: dict[str, str] | None = None) -> None:
        self.records.append((float(value), attributes))


class InMemoryMetricsProvider(MetricsProvider):
    def __init__(self) -> None:
        self.counters: dict[str, InMemoryCounter] = {}
        self.histograms: dict[str, InMemoryHistogram] = {}

    def create_counter(self, name: str, description: str = "") -> MetricCounter:
        if name not in self.counters:
            self.counters[name] = InMemoryCounter(name)
        return self.counters[name]

    def create_histogram(self, name: str, description: str = "") -> MetricHistogram:
        if name not in self.histograms:
            self.histograms[name] = InMemoryHistogram(name)
        return self.histograms[name]
