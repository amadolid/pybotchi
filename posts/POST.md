## Core Architecture:

**Nested Intent-Based Supervisor Agent Architecture**

## What Core Features Are Currently Supported?

### Lifecycle

- Every agent utilizes pre, core, fallback, and post executions.

### Sequential Combination

- Multiple agent executions can be performed in sequence within a single tool call.

### Concurrent Combination

- Multiple agent executions can be performed concurrently in a single tool call, using either threads or tasks.

### Sequential Iteration

- Multiple agent executions can be performed via iteration.

### MCP Integration

- **As Server**: Existing agents can be mounted to FastAPI to become an MCP endpoint.
- **As Client**: Agents can connect to an MCP server and integrate its tools.
  - Tools can be overridden.

### Combine/Override/Extend/Nest Everything

- Everything is configurable.

## How to Declare an Agent?

### LLM Declaration

```python
from pybotchi import LLM
from langchain_openai import ChatOpenAI

LLM.add(
    base = ChatOpenAI(.....)
)
```

### Imports

```
from pybotchi import Action, ActionReturn, Context
```

### Agent Declaration

```python
class Translation(Action):
    """Translate to specified language."""

    async def pre(self, context):
        message = await context.llm.ainvoke(context.prompts)
        await context.add_response(self, message.text)
        return ActionReturn.GO
```

- This can already work as an agent. `context.llm` will use the base LLM.
- You have complete freedom here: call another agent, invoke LLM frameworks, execute tools, perform mathematical operations, call external APIs, or save to a database. There are no restrictions.

### Agent Declaration with Fields

```python
class MathProblem(Action):
    """Solve math problems."""

    answer: str

    async def pre(self, context):
        await context.add_response(self, self.answer)
        return ActionReturn.GO
```

- Since this agent requires arguments, you need to attach it to a parent `Action` to use it as an agent. Don't worry, it doesn't need to have anything specific; just add it as a child `Action`, and it should work fine.
- You can use `pydantic.Field` to add descriptions of the fields if needed.

### Multi-Agent Declaration

```python
class MultiAgent(Action):
    """Solve math problems, translate to specific language, or both."""

    class SolveMath(MathProblem):
        pass

    class Translate(Translation):
        pass
```

- This is already your multi-agent. You can use it as is or extend it further.
- You can still override it: change the docstring, override pre-execution, or add post-execution. There are no restrictions.

### How to Run?

```python
import asyncio

async def test():
    context = Context(
        prompts=[
            {"role": "system", "content": "You're an AI that can solve math problems and translate any request. You can call both if necessary."},
            {"role": "user", "content": "4 x 4 and explain your answer in filipino"}
        ],
    )
    action, result = await context.start(MultiAgent)
    print(context.prompts[-1]["content"])
asyncio.run(test())
```

### Result

Ang sagot sa 4 x 4 ay 16.

Paliwanag: Ang ibig sabihin ng "4 x 4" ay apat na grupo ng apat. Kung bibilangin natin ito: 4 + 4 + 4 + 4 = 16. Kaya, ang sagot ay 16.

### How Pybotchi Improves Our Development and Maintainability, and How It Might Help Others Too

Since our agents are now modular, each agent will have isolated development. Agents can be maintained by different developers, teams, departments, organizations, or even communities.

**Every agent can have its own abstraction that won't affect others. You might imagine an agent maintained by a community that you import and attach to your own agent. You can customize it in case you need to patch some part of it.**

**Enterprise services can develop their own translation layer, similar to MCP, but without requiring MCP server/client complexity.**

---

### Other Examples

- **Don't forget LLM declaration!**

#### MCP Integration (as Server)

```python
from contextlib import AsyncExitStack, asynccontextmanager
from fastapi import FastAPI
from pybotchi import Action, ActionReturn, mount_mcp_groups

class TranslateToEnglish(Action):
    """Translate sentence to english."""

    __groups__ = {"mcp": {"your_endpoint"}}

    sentence: str

    async def pre(self, context):
        message = await context.llm.ainvoke(
            f"Translate this to english: {self.sentence}"
        )
        await context.add_response(self, message.text)
        return ActionReturn.GO


@asynccontextmanager
async def lifespan(app):
    """Override life cycle."""
    async with AsyncExitStack() as stack:
        await start_mcp_servers(app, stack)
        yield


app = FastAPI(lifespan=lifespan)
```

```bash
from asyncio import run

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client(
        "http://localhost:8000/your_endpoint/mcp",
    ) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            response = await session.call_tool(
                "TranslateToEnglish",
                arguments={
                    "sentence": "Kamusta?",
                },
            )
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            print(response.content[0].text)

run(main())
```

#### Result

```
Available tools: ['TranslateToEnglish']
"Kamusta?" in English is "How are you?"
```

#### MCP Integration (as Client)

```python
from asyncio import run

from pybotchi import (
    ActionReturn,
    Context,
    MCPAction,
    MCPConnection,
    graph,
)


class GeneralChat(MCPAction):
    """Casual Generic Chat."""

    __mcp_connections__ = [
        MCPConnection(
            "YourAdditionalIdentifier",
            "http://0.0.0.0:8000/your_endpoint/mcp",
            require_integration=False,
        )
    ]


async def test() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {"role": "system", "content": ""},
            {"role": "user", "content": "What is the english of `Kamusta?`"},
        ]
    )
    await context.start(GeneralChat)
    print(context.prompts[-1]["content"])

    general_chat_graph = await graph(GeneralChat)
    print(general_chat_graph.flowchart())


run(test())
```

#### Result (_Response and Mermaid flowchart_)

```
"Kamusta?" in English is "How are you?"
flowchart TD
mcp.YourAdditionalIdentifier.Translatetoenglish[mcp.YourAdditionalIdentifier.Translatetoenglish]
__main__.GeneralChat[__main__.GeneralChat]
__main__.GeneralChat --> mcp.YourAdditionalIdentifier.Translatetoenglish
```

- You may add post execution to adjust the final response if needed

#### Iteration

```python
class MultiAgent(Action):
    """Solve math problems, translate to specific language, or both."""

    __max_child_iteration__ = 5

    class SolveMath(MathProblem):
        pass

    class Translate(Translation):
        pass
```

- This will allow iteration approach similar to other framework

#### Concurrent and Post-Execution Utilization

```python
class GeneralChat(Action):
    """Casual Generic Chat."""

    class Joke(Action):
        """This Assistant is used when user's inquiry is related to generating a joke."""

        __concurrent__ = True

        async def pre(self, context):
            print("Executing Joke...")
            message = await context.llm.ainvoke("generate very short joke")
            await context.add_usage(self, context.llm.model_name, message.usage_metadata)

            await context.add_response(self, message.text)
            print("Done executing Joke...")
            return ActionReturn.GO

    class StoryTelling(Action):
        """This Assistant is used when user's inquiry is related to generating stories."""

        __concurrent__ = True

        async def pre(self, context):
            print("Executing StoryTelling...")
            message = await context.llm.ainvoke("generate a very short story")
            await context.add_usage(self, context.llm.model_name, message.usage_metadata)

            await context.add_response(self, message.text)
            print("Done executing StoryTelling...")
            return ActionReturn.GO

    async def post(self, context):
        print("Executing post...")
        message = await context.llm.ainvoke(context.prompts)
        await context.add_message(ChatRole.ASSISTANT, message.text)
        print("Done executing post...")
        return ActionReturn.END

async def test() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {"role": "system", "content": ""},
            {
                "role": "user",
                "content": "Tell me a joke and incorporate it on a very short story",
            },
        ],
    )
    await context.start(GeneralChat)
    print(context.prompts[-1]["content"])

run(test())
```

#### Result (_Response and Mermaid flowchart_)

```
Executing Joke...
Executing StoryTelling...
Done executing Joke...
Done executing StoryTelling...
Executing post...
Done executing post...
Here’s a very short story with a joke built in:

Every morning, Mia took the shortcut to school by walking along the two white chalk lines her teacher had drawn for a math lesson. She said the lines were “parallel” and explained, “Parallel lines have so much in common; it’s a shame they’ll never meet.” Every day, Mia wondered if maybe, just maybe, she could make them cross—until she realized, with a smile, that like some friends, it’s fun to walk side by side even if your paths don’t always intersect!
```

#### Complex Overrides and Nesting

```python
class Override(MultiAgent):
    SolveMath = None  # Remove action

    class NewAction(Action):  # Add new action
        pass

    class Translation(Translate):  # Override existing
        async def pre(self, context):
            # override pre execution

        class ChildAction(Action): # Add new action in existing Translate

            class GrandChildAction(Action):
                # Nest if needed
                # Declaring it outside this class is recommend as it's more maintainable
                # You can use it as base class
                pass

    # MultiAgent might already overrided the Solvemath.
    # In that case, you can use it also as base class
    class SolveMath2(MultiAgent.SolveMath):
        # Do other override here
        pass
```

#### Manage prompts / Call different framework

```python
class YourAction(Action):
    """Description of your action."""


    async def pre(self, context):
        # manipulate
        prompts = [{
            "content": "hello",
            "role": "user"
        }]
        # prompts = itertools.islice(context.prompts, 5)
        # prompts = [
        #    *context.prompts,
        #    {
        #        "content": "hello",
        #        "role": "user"
        #    },
        # ]
        # prompts = [
        #    *some_generator_prompts(),
        #    *itertools.islice(context.prompts, 3)
        # ]

        # default using langchain
        message = await context.llm.ainvoke(prompts)
        content = message.text

        # other langchain library
        message = await custom_base_chat_model.ainvoke(prompts)
        content = message.text

        # Langgraph
        APP = your_graph.compile()
        message = await APP.ainvoke(prompts)
        content = message["messages"][-1].text

        # CrewAI
        content = await crew.kickoff_async(inputs=your_customized_prompts)


        await context.add_response(self, content)
```

#### Overidding Tool Selection

```python
class YourAction(Action):
    """Description of your action."""


    class Action1(Action):
        pass
    class Action2(Action):
        pass
    class Action3(Action):
        pass

    # this will always select Action1
    async def child_selection(
        self,
        context: Context,
        child_actions: ChildActions | None = None,
    ) -> tuple[list["Action"], str]:
        """Execute tool selection process."""

        # Getting child_actions manually
        child_actions = await self.get_child_actions(context)

        # Do your process here

        return [self.Action1()], "Your fallback message here incase nothing is selected"
```

## Repository Examples

### **Basic**

- [`tiny.py`](https://github.com/amadolid/pybotchi/blob/master/examples/tiny.py) - Minimal implementation to get you started
- [`full_spec.py`](https://github.com/amadolid/pybotchi/blob/master/examples/full_spec.py) - Complete feature demonstration

### **Flow Control**

- [`sequential_combination.py`](https://github.com/amadolid/pybotchi/blob/master/examples/sequential_combination.py) - Multiple actions in sequence
- [`sequential_iteration.py`](https://github.com/amadolid/pybotchi/blob/master/examples/sequential_iteration.py) - Iterative action execution
- [`nested_combination.py`](https://github.com/amadolid/pybotchi/blob/master/examples/nested_combination.py) - Complex nested structures

### **Concurrency**

- [`concurrent_combination.py`](https://github.com/amadolid/pybotchi/blob/master/examples/concurrent_combination.py) - Parallel action execution
- [`concurrent_threading_combination.py`](https://github.com/amadolid/pybotchi/blob/master/examples/concurrent_threading_combination.py) - Multi-threaded processing

### **Real-World Applications**

- [`interactive_agent.py`](https://github.com/amadolid/pybotchi/blob/master/examples/interactive_agent.py) - Real-time WebSocket communication
- [`jira_agent.py`](https://github.com/amadolid/pybotchi/blob/master/examples/jira_agent.py) - Integration with MCP Atlassian server
- [`agent_with_mcp.py`](https://github.com/amadolid/pybotchi/blob/master/examples/agent_with_mcp.py) - Hosting Actions as MCP tools

### **Framework Comparison (Get Weather)**

- [`Pybotchi`](https://github.com/amadolid/pybotchi/blob/master/examples/vs/pybotchi_approach.py)
- [`LangGraph`](https://github.com/amadolid/pybotchi/blob/master/examples/vs/langgraph_approach.py)

Feel free to comment or message me for examples. I hope this helps with your development too.

https://github.com/amadolid/pybotchi
