"""MCP Server Action."""

from mcp_prerequisite import Action, ActionReturn, ChatRole, Context, build_mcp_app

from pydantic import Field

from uvicorn import run


class MathProblem(Action):
    """Solve the math problem."""

    __groups__ = {"mcp": {"group-1"}}

    equation: str = Field(description="The mathematical equation to solve (e.g., '2x + 5')")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(f"Solve `{self.equation}`")
        await context.add_usage(self, context.llm.model_name, message.usage_metadata)
        await context.add_response(self, message.text)
        return ActionReturn.GO


class Translation(Action):
    """Translate to specific language."""

    __groups__ = {"mcp": {"group-1"}}

    message: str = Field(description="The text content to be translated.")
    language: str = Field(description="The ISO code or name of the target language.")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(f"Translate `{self.message}` to {self.language}")
        await context.add_usage(self, context.llm.model_name, message.usage_metadata)
        await context.add_response(self, message.text)

        return ActionReturn.GO


class JokeWithStoryTelling(Action):
    """Tell Joke or Story."""

    __groups__ = {"mcp": {"group-1", "group-2"}}

    query: str

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        await context.add_message(ChatRole.USER, self.query)
        return ActionReturn.GO

    class Joke(Action):
        """Generate a joke."""

        __concurrent__ = True

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            print("Executing Joke...")
            message = await context.llm.ainvoke("generate very short joke")
            await context.add_usage(self, context.llm.model_name, message.usage_metadata)

            await context.add_response(self, message.text)
            print("Done executing Joke...")
            return ActionReturn.GO

    class StoryTelling(Action):
        """Tell a story."""

        __concurrent__ = True

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            print("Executing StoryTelling...")
            message = await context.llm.ainvoke("generate a very short story")
            await context.add_usage(self, context.llm.model_name, message.usage_metadata)

            await context.add_response(self, message.text)
            print("Done executing StoryTelling...")
            return ActionReturn.GO

    async def post(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        print("Executing post...")
        message = await context.llm.ainvoke(context.prompts)
        await context.add_usage(self, context.llm.model_name, message.usage_metadata, "combine")
        await context.add_message(ChatRole.ASSISTANT, message.text)
        print("Done executing post...")
        return ActionReturn.END


##################################################################################
#                                   Direct MCP                                   #
#                      SSE paths /group-1/sse & /group-2/sse                     #
#                Streamable HTTP paths /group-1/mcp & /group-2/mcp               #
##################################################################################

app = build_mcp_app(transport="streamable-http")

if __name__ == "__main__":
    run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )

##################################################################################
#                                FastAPI Mounting                                #
##################################################################################

# from collections.abc import AsyncGenerator
# from contextlib import asynccontextmanager

# from fastapi import FastAPI

# from pybotchi.mcp import mount_mcp_app


# @asynccontextmanager
# async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
#     """Override life cycle."""
#     async with mount_mcp_app(app, transport="streamable-http"):
#         yield


# app = FastAPI(lifespan=lifespan)
# if __name__ == "__main__":
#     run(
#         app,
#         host="127.0.0.1",
#         port=8000,
#         log_level="info",
#     )
