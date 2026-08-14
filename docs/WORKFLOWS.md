# Workflows & Deterministic Sagas

AegisMCP uses the `WorkflowEngine` to implement the **Saga Pattern**.

## Why Sagas?

In a multi-agent or multi-tool system, tasks often require multiple sequential steps (e.g., Book Flight, Reserve Hotel, Charge Credit Card). 

If "Charge Credit Card" fails, you can't simply throw an error—you must roll back the hotel and flight!

## Implementation

```python
class BookFlightStep:
    async def execute(self, ctx: AegisContext):
        return await flight_api.book()
        
    async def compensate(self, ctx: AegisContext):
        # Triggered automatically if ANY subsequent step fails!
        await flight_api.cancel()
```

AegisMCP executes these sagas deterministically, ensuring your enterprise system always returns to a stable state.
