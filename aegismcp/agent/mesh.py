from aegismcp.agent.core import AegisAgent
from aegismcp.kernel.context import AegisContext
from aegismcp.tools.descriptor import ToolDescriptor


def agent_as_tool(name: str, description: str, agent: AegisAgent) -> ToolDescriptor:
    """Wraps an AegisAgent to be exposed as a callable Tool."""

    async def fn(query: str, ctx: AegisContext) -> str:
        res = await agent.run(query, ctx)
        return res.content

    return ToolDescriptor(
        name=name,
        description=description,
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        output_schema=None,
        timeout_seconds=60.0,
        max_retries=0,
        retry_delay_seconds=0,
        is_idempotent=False,
        required_permissions=frozenset(),
        audit_level="FULL",
        fn=fn,
    )
