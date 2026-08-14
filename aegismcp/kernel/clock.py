import time
from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    """Injectable clock for deterministic testing of deadlines and timeouts."""

    def now(self) -> datetime: ...

    def monotonic(self) -> float: ...


class RealClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()


class FakeClock(Clock):
    def __init__(self, start_time: datetime | None = None) -> None:
        self._now = start_time or datetime.now(UTC)
        self._monotonic = 0.0

    def now(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._monotonic

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
        self._monotonic += seconds
