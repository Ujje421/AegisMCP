import asyncio
from dataclasses import dataclass

from aegismcp.client.core import AegisClient
from aegismcp.kernel.context import AegisContext
from aegismcp.kernel.errors import AegisError
from aegismcp.tools.descriptor import ToolDescriptor

from .memory import InMemoryMemory, Memory
from .models import GenerationConfig, Message, ModelProvider
from .selector import AllToolsSelector, ToolSelector


class AgentError(AegisError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


@dataclass(frozen=True)
class AgentResult:
    content: str
    turns: int


class AegisAgent:
    def __init__(
        self,
        model: ModelProvider,
        client: AegisClient,
        tool_registry: dict[str, ToolDescriptor],
        selector: ToolSelector | None = None,
        memory: Memory | None = None,
        config: GenerationConfig | None = None,
        max_turns: int = 10,
    ):
        self.model = model
        self.client = client
        self.tool_registry = tool_registry
        self.selector = selector or AllToolsSelector()
        self.memory = memory or InMemoryMemory()
        self.config = config or GenerationConfig()
        self.max_turns = max_turns

    async def run(self, user_message: str, ctx: AegisContext) -> AgentResult:
        messages = [Message.user(user_message)]

        for turn in range(self.max_turns):
            relevant_tools = await self.selector.select(messages, self.tool_registry)

            response = await self.model.generate(messages, relevant_tools, self.config, ctx)

            if not response.tool_calls:
                return AgentResult(content=response.content, turns=turn + 1)

            tool_results = await asyncio.gather(
                *[
                    self.client.call_tool(
                        name=tc.name,
                        arguments=tc.arguments,
                    )
                    for tc in response.tool_calls
                ]
            )

            messages.append(response.as_assistant_message())

            for tr, tc in zip(tool_results, response.tool_calls):
                content = str(tr.get("content", tr)) if isinstance(tr, dict) else str(tr)
                messages.append(Message.tool(f"Result for {tc.name}: {content}"))

        raise AgentError("Max turns exceeded")
