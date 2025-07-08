"""Testing."""

from asyncio import run
from datetime import datetime
from typing import Annotated, Literal

from langchain_core.tools import tool

from langchain_openai import AzureChatOpenAI

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from pybotchi.settings import getenv

from typing_extensions import TypedDict


class State(TypedDict):
    """State Class."""

    messages: Annotated[list, add_messages]


graph = StateGraph(State)


@tool
def get_weather(location: str) -> str:
    """Call to get the current weather."""
    if location.lower() in ["yorkshire"]:
        return "It's cold and wet."
    else:
        return "It's warm and sunny."


llm = AzureChatOpenAI(
    api_key=getenv("CHAT_KEY"),
    azure_endpoint=getenv("CHAT_ENDPOINT"),
    azure_deployment=getenv("CHAT_DEPLOYMENT"),
    model=getenv("CHAT_MODEL"),
    openai_api_version=getenv("CHAT_VERSION"),
    temperature=int(getenv("CHAT_TEMPERATURE", "1")),
    stream_usage=True,
    verbose=True,
)

tools = [get_weather]

llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools)

graph.add_node("tool_node", tool_node)


async def prompt_node(state: State) -> State:
    """Trigger Invoke."""
    new_message = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [new_message]}


graph.add_node("prompt_node", prompt_node)


def conditional_edge(state: State) -> Literal["tool_node", "__end__"]:
    """Trigger Conditional Edge."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    else:
        return "__end__"


graph.add_conditional_edges("prompt_node", conditional_edge)
graph.add_edge("tool_node", "prompt_node")
graph.set_entry_point("prompt_node")
APP = graph.compile()

total = 0.0
for _i in range(10):
    now = datetime.now().timestamp()
    new_state = run(APP.ainvoke({"messages": ["Whats the weather in yorkshire?"]}))
    print(new_state["messages"][-1].content)
    total += datetime.now().timestamp() - now
print(total / 10)
