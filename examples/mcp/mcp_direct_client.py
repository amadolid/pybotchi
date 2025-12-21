"""Direct MCP Client."""

from asyncio import run

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main() -> None:
    """Test."""
    print("#######################################################################")
    print("#                             MCP Group 1                             #")
    print("#######################################################################")
    async with streamablehttp_client("http://localhost:8000/group-1/mcp") as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(
                "Tools:\n",
                "\n".join(
                    f"{tool.name}: {tool.description}"
                    for tool in (await session.list_tools()).tools
                ),
                "\n----------------------------",
                sep="",
            )
            print(
                "MathProblem:",
                (
                    await session.call_tool(
                        name="MathProblem", arguments={"equation": "10 x 10"}
                    )
                )
                .content[0]
                .text,  # type: ignore[union-attr]
            )
            print(
                "Translation:",
                (
                    await session.call_tool(
                        name="Translation",
                        arguments={"message": "Kamusta?", "language": "English"},
                    )
                )
                .content[0]
                .text,  # type: ignore[union-attr]
            )
            print(
                "JokeWithStoryTelling:",
                (
                    await session.call_tool(
                        name="JokeWithStoryTelling",
                        arguments={
                            "query": "Tell me a joke and incorporate it on a very short story"
                        },
                    )
                )
                .content[0]
                .text,  # type: ignore[union-attr]
            )

    print("#######################################################################")
    print("#              MCP Group 2 (No MathProblem & Translation)             #")
    print("#######################################################################")
    async with streamablehttp_client("http://localhost:8000/group-2/mcp") as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(
                "Tools:\n",
                "\n".join(
                    f"{tool.name}: {tool.description}"
                    for tool in (await session.list_tools()).tools
                ),
                "\n----------------------------",
                sep="",
            )
            print(
                "MathProblem:",
                (
                    await session.call_tool(
                        name="MathProblem", arguments={"equation": "10 x 10"}
                    )
                )
                .content[0]
                .text,  # type: ignore[union-attr]
            )
            print(
                "Translation:",
                (
                    await session.call_tool(
                        name="Translation",
                        arguments={"message": "Kamusta?", "language": "English"},
                    )
                )
                .content[0]
                .text,  # type: ignore[union-attr]
            )
            print(
                "JokeWithStoryTelling:",
                (
                    await session.call_tool(
                        name="JokeWithStoryTelling",
                        arguments={
                            "query": "Tell me a joke and incorporate it on a very short story"
                        },
                    )
                )
                .content[0]
                .text,  # type: ignore[union-attr]
            )


run(main())
