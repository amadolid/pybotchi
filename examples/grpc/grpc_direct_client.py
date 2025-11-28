"""The Python AsyncIO implementation of the GRPC hellostreamingworld.MultiGreeter client."""

from asyncio import Queue, run
from collections.abc import AsyncGenerator
from json import dumps

from google.protobuf.json_format import MessageToDict

from grpc.aio import insecure_channel

from pybotchi.grpc.pybotchi_pb2 import ActionListRequest, ActionListResponse, Event
from pybotchi.grpc.pybotchi_pb2_grpc import PyBotchiGRPCStub


async def stream(queue: Queue[Event]) -> AsyncGenerator[Event, None]:
    """Stream request."""
    while que := await queue.get():
        yield que


async def connect() -> None:
    """Test connect."""
    action_list: ActionListResponse
    async with insecure_channel("localhost:50051") as channel:
        stub = PyBotchiGRPCStub(channel)

        action_list = await stub.action_list(ActionListRequest(group="group-1"))
        print(action_list.actions)
        action_list = await stub.action_list(ActionListRequest(group="group-2"))
        print(action_list.actions)

        queue = Queue[Event]()
        await queue.put(
            Event(
                name="init",
                data={
                    "group": "group-1",
                    "context": {
                        "prompts": [
                            {
                                "role": "system",
                                "content": "",
                            },
                            {
                                "role": "user",
                                "content": "translate `How are you` in filipino",
                            },
                        ]
                    },
                },
            )
        )
        await queue.put(
            Event(
                name="execute",
                data={
                    "name": "Translation",
                },
            )
        )

        async for event in stub.connect(stream(queue)):
            if event.name == "close":
                print(dumps(MessageToDict(event), indent=2))


if __name__ == "__main__":
    run(connect())
