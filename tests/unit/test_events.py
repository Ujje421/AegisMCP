import pytest

from aegismcp.kernel.events import EventBus


class MyEvent:
    pass

class AnotherEvent:
    pass

@pytest.mark.asyncio
async def test_event_bus():
    bus = EventBus()
    
    received_events = []
    
    async def handler1(event: MyEvent):
        received_events.append(1)
        
    async def handler2(event: MyEvent):
        received_events.append(2)
        
    bus.subscribe(MyEvent, handler1)
    bus.subscribe(MyEvent, handler2)
    
    await bus.publish(MyEvent())
    
    # Both handlers should have run
    assert len(received_events) == 2
    assert 1 in received_events
    assert 2 in received_events

@pytest.mark.asyncio
async def test_event_bus_no_handlers():
    bus = EventBus()
    # Should not raise
    await bus.publish(MyEvent())

@pytest.mark.asyncio
async def test_event_bus_different_events():
    bus = EventBus()
    received = []
    
    async def handler(event: MyEvent):
        received.append("my")
        
    bus.subscribe(MyEvent, handler)
    
    await bus.publish(AnotherEvent())
    assert len(received) == 0
    
    await bus.publish(MyEvent())
    assert len(received) == 1
