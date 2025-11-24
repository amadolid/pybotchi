"""Direct MCP Client."""

from asyncio import run

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main() -> None:
    """Test."""
    async with streamablehttp_client("http://localhost:8000/test/mcp") as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print((await session.list_tools()).model_dump_json(indent=1))
            print(
                (
                    await session.call_tool(
                        name="NestedAgent", arguments={"query": "hello"}
                    )
                ).model_dump_json(indent=1)
            )
            print(
                (await session.call_tool(name="SingleAction")).model_dump_json(indent=1)
            )

    async with streamablehttp_client("http://localhost:8000/test2/mcp") as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print((await session.list_tools()).model_dump_json(indent=1))
            print(
                (
                    await session.call_tool(
                        name="NestedAgent", arguments={"query": "hello"}
                    )
                ).model_dump_json(indent=1)
            )
            print(
                (await session.call_tool(name="SingleAction")).model_dump_json(indent=1)
            )


run(main())
