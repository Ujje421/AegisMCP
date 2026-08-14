import pytest
from aegismcp.protocol.lifecycle import SessionLifecycle, SessionState, StateTransitionEvent
from aegismcp.kernel.events import EventBus

@pytest.mark.asyncio
async def test_lifecycle():
    bus = EventBus()
    events = []
    
    async def on_transition(event: StateTransitionEvent):
        events.append(event)
        
    bus.subscribe(StateTransitionEvent, on_transition)
    
    lifecycle = SessionLifecycle(bus)
    assert lifecycle.state == SessionState.CONNECTING
    
    await lifecycle.transition_to(SessionState.READY)
    assert lifecycle.state == SessionState.READY
    assert len(events) == 1
    assert events[0].old_state == SessionState.CONNECTING
    assert events[0].new_state == SessionState.READY
