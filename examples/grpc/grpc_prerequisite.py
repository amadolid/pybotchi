"""Sample LLMs."""

from os import getenv

from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI

from pybotchi import Action, ActionReturn, ChatRole, Context as BaseContext, LLM
from pybotchi.grpc import (
    GRPCAction,
    GRPCConnection,
    GRPCContext as BaseGRPCContext,
    GRPCIntegration,
    GRPCRemoteAction,
    graph,
)
from pybotchi.grpc.pybotchi_pb2 import Event

load_dotenv()

LLM.add(
    base=AzureChatOpenAI(
        api_key=getenv("CHAT_KEY"),  # type: ignore[arg-type]
        azure_endpoint=getenv("CHAT_ENDPOINT"),
        azure_deployment=getenv("CHAT_DEPLOYMENT"),
        model=getenv("CHAT_MODEL"),
        api_version=getenv("CHAT_VERSION"),
        temperature=int(getenv("CHAT_TEMPERATURE", "1")),
        stream_usage=True,
    )
)
Context = BaseContext[AzureChatOpenAI]
GRPCContext = BaseGRPCContext[AzureChatOpenAI]

__all__ = [
    "Action",
    "ActionReturn",
    "ChatRole",
    "Context",
    "GRPCAction",
    "GRPCConnection",
    "GRPCContext",
    "GRPCIntegration",
    "GRPCRemoteAction",
    "graph",
    "Event",
]
