"""User APIs."""

from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from pybotchi import Action, ActionReturn, ChatRole, Context, start_mcp_servers

from pydantic import Field

from uvicorn import run


class SingleAction(Action):
    """You're an AI agent the generates random number."""

    __mcp_groups__ = ["test2"]

    async def pre(self, context: Context) -> ActionReturn:
        """Run preperation."""
        await context.add_response(self, "10000")
        return ActionReturn.END


class NestedAgent(Action):
    """You're an AI the can solve math problem and translate any request."""

    query: str = Field(description="User question.")

    __mcp_groups__ = ["test"]

    async def pre(self, context: Context) -> ActionReturn:
        """Run preperation."""
        await context.add_message(ChatRole.USER, self.query)
        return ActionReturn.GO

    class MathProblem(Action):
        """Solve the math problem."""

        answer: str = Field(description="Your answer to the math problem")

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            await context.add_response(self, self.answer)
            return ActionReturn.GO

    class Translation(Action):
        """Translate to specific language."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            message = await context.llm.ainvoke(context.prompts)
            context.add_usage(self, context.llm, message.usage_metadata)
            await context.add_response(self, message.text())
            return ActionReturn.GO


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, FastAPI]:
    """Override life cycle."""
    async with AsyncExitStack() as stack:
        await start_mcp_servers(app, stack)

        yield


app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
