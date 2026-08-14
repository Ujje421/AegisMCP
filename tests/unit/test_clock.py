from datetime import UTC, datetime

from aegismcp.kernel.clock import FakeClock, RealClock


def test_real_clock():
    clock = RealClock()
    assert isinstance(clock.now(), datetime)
    assert clock.now().tzinfo == UTC
    assert isinstance(clock.monotonic(), float)

def test_fake_clock():
    start = datetime(2025, 1, 1, tzinfo=UTC)
    clock = FakeClock(start)
    
    assert clock.now() == start
    assert clock.monotonic() == 0.0
    
    clock.advance(1.5)
    
    assert clock.now().second == 1
    assert clock.now().microsecond == 500000
    assert clock.monotonic() == 1.5
