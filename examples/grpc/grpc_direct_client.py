"""The Python AsyncIO implementation of the GRPC hellostreamingworld.MultiGreeter client."""

from asyncio import Queue, run
from collections.abc import AsyncGenerator

from grpc.aio import insecure_channel

from pybotchi.grpc.pybotchi_pb2 import ActionListRequest, ActionListResponse, Event
from pybotchi.grpc.pybotchi_pb2_grpc import PyBotchiGRPCStub


async def stream(queue: Queue[Event]) -> AsyncGenerator[Event]:
    """Stream request."""
    while que := await queue.get():
        yield que


async def connect() -> None:
    """Test connect."""
    async with insecure_channel("localhost:50051") as channel:
        stub = PyBotchiGRPCStub(channel)

        queue = Queue[Event]()
        await queue.put(Event(name="connect", data={}))

        async for response in stub.connect(stream(queue)):
            print(response)

        a: ActionListResponse = await stub.action_list(ActionListRequest(group="test"))
        print(a.actions)
        a = await stub.action_list(ActionListRequest(group="test2"))
        print(a.actions)


if __name__ == "__main__":
    run(connect())
