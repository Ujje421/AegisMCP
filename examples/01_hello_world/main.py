import asyncio
from aegismcp.server.app import AegisMCP

app = AegisMCP("HelloWorld")

@app.tool(description="Say hello")
async def say_hello(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    asyncio.run(app.run_stdio())
