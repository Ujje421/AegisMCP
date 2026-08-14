import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

TEvent = TypeVar("TEvent")
EventHandler = Callable[[TEvent], Awaitable[None]]

class EventBus:
    """
    Internal event bus for decoupled asynchronous communication.
    
    Not exposed to framework users. Used for internal observability, 
    security audits, and state transitions.
    """
    
    def __init__(self) -> None:
        self._subscribers: dict[type[Any], list[EventHandler[Any]]] = defaultdict(list)
        
    def subscribe(self, event_type: type[TEvent], handler: EventHandler[TEvent]) -> None:
        """Subscribe an async handler to a specific event type."""
        self._subscribers[event_type].append(handler)
        
    async def publish(self, event: TEvent) -> None:
        """Publish an event to all subscribed handlers concurrently."""
        handlers = self._subscribers.get(type(event), [])
        if not handlers:
            return
            
        await asyncio.gather(*(handler(event) for handler in handlers))
