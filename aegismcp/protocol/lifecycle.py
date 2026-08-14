from enum import Enum, auto

from aegismcp.kernel.events import EventBus


class SessionState(Enum):
    CONNECTING = auto()
    NEGOTIATING = auto()
    READY = auto()
    CLOSING = auto()
    CLOSED = auto()

class StateTransitionEvent:
    def __init__(self, old_state: SessionState, new_state: SessionState):
        self.old_state = old_state
        self.new_state = new_state

class SessionLifecycle:
    def __init__(self, bus: EventBus):
        self._state = SessionState.CONNECTING
        self._bus = bus
        
    @property
    def state(self) -> SessionState:
        return self._state
        
    async def transition_to(self, new_state: SessionState) -> None:
        old_state = self._state
        self._state = new_state
        await self._bus.publish(StateTransitionEvent(old_state, new_state))
