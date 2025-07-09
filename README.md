# 🤖 Pybotchi

> _A deterministic, intent-based AI agent builder with no restrictions—supports any framework and prioritizes human-reasoning approach and interactive real-time client communication._

---

## 🎯 Why This Library Exists

The AI agent landscape is rich with powerful frameworks—**LangGraph**, **CrewAI**, and countless others. Each brings unique strengths and trade-offs. **This library aims to support them all, but with a fundamental twist.**

### 🧠 The Problem with Current LLMs

Current LLMs face a **critical limitation**: **reasoning and thinking capabilities remain constrained**, even when enhanced with iterative workflows. Emerging research reinforces this reality—LLMs don't truly possess reasoning power in the way we might expect.

But here's what they _excel_ at: **intent detection and translation**.

Since modern LLMs are extensively trained on natural language, we can leverage this core strength rather than fighting their limitations.

### 💡 Our Philosophy

> **Humans should handle the reasoning. AI should detect intent and translate natural language into processable data.**

This approach unlocks AI's true potential through **tool call chaining**—where AI becomes the perfect interpreter between human intent and computational action.

---

## 🚀 The Vision

_Building agents that combine human intelligence with AI precision._

### ⚡ Lightweight by Design

Pybotchi stays minimal with only **3 core classes**:

- **`Action`** - Describes the intent
- **`Context`** - Holds everything
- **`LLM`** - LLM client instance holder

### 🔧 Everything is Overridable & Extendable

**Maximum flexibility, zero lock-in.** Everything is designed to be overridable and extendable to foster a community where developers can publish their own Actions associated with specific Intents—enabling everyone to reuse or override them for their unique use cases. Currently, the default tool call invocation uses **LangChain's BaseChatModel**. But you're not stuck with it—override this function and use native SDKs like **OpenAI** directly.

---

## 🚀 Let's Start with the Basics

### **Prerequisite**

First, you need to import the LLM Class and set the base LLM to be used in Children Selection. You can use alternative frameworks other than LangChain, but you'll also need to override the child selection flow. We'll discuss that later.

<details>
  <summary>Add base LLM</summary>

```python
from os import getenv
from langchain_openai import AzureChatOpenAI
from pybotchi import LLM

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
```

</details>

### **Action 1: Mathematical Problem Solver**

This action handles mathematical problem-solving intents. It takes a mathematical problem, processes it, and returns the solution directly through the pre-process phase:

<details>
  <summary>Add MathProblem Action</summary>

```python
from pybotchi import Action, ActionReturn, Context

class MathProblem(Action):
    """Solve mathematical problem."""

    answer: str = Field(description="You answer to the math problem")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        await context.add_response(self, self.answer)
        return ActionReturn.END
```

</details>

### **Action 2: Translation Service**

This action handles translation intents. It leverages the LLM to translate content and properly tracks usage metrics:

<details>
  <summary>Add Translation Action</summary>

```python
from pybotchi import Action, ActionReturn, Context

class Translation(Action):
    """Translate to specified language."""

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(context.prompts)
        context.add_usage(self, context.llm, message.usage_metadata)
        await context.add_response(self, message.content)
        return ActionReturn.GO
```

</details>

This could already work on its own, but it's only one intent per action.

### **Creating a Multi-Intent Agent**

Now we'll merge these into a single Agent that can handle multiple intents:

<details>
  <summary>Build Agent</summary>

```python
from pybotchi import Action, ActionReturn, Context

# import Translation
# import MathProblem as _MathProblem

class Agent(Action):
    """AI Assistant for solving math problem and translation."""

    class MathProblem(_MathProblem):
        """Solve mathematical problem."""
        # Override your docstring here if necessary. Put pass if you want to use the same docstring

    class TranslateRequest(Translation):
        pass
```

</details>

### **How to Run It**

You need to build your context. This includes chat history, metadata, and additional useful attributes. We also prioritize async because most AI agents are integrated in services, most commonly web services. Since most of the time we don't host LLMs, we are bound to call network requests which are IO Bound. This is the reason why we prioritize async.

There's a hard rule also on this library: **Context should always have the system prompt entry, even if it's empty content.** This is to have a more consistent way of controlling system prompt. Will give example later.

<details>
  <summary>Run the Agent</summary>

```python
from asyncio import run

from pybotchi import Context,

async def test() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": "system", # or pybotchi.ChatRole.SYSTEM
                "content": "You're an AI the can solve math problem and translate any request.",
            },
            {
                "role": "user", # or pybotchi.ChatRole.USER
                "content": "4 x 4 and explain your answer in filipino",
            },
        ],
    )
    action, result = await context.start(GeneralChat)
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))


run(test())
```

</details>

<details>
  <summary><b>Results</b></summary>

```json
[
    {
        "role": "system",
        "content": "You're an AI the can solve math problem and translate any request."
    },
    {
        "role": "user",
        "content": "4 x 4 and explain your answer in filipino"
    },
    {
        "content": "",
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_d1b652297be94b6f8999dc8b53005872",
                "function": {
                    "name": "MathProblem",
                    "arguments": "{\"answer\":\"4 x 4 = 16\"}"
                },
                "type": "function"
            }
        ]
    },
    {
        "content": "4 x 4 = 16",
        "role": "tool",
        "tool_call_id": "call_d1b652297be94b6f8999dc8b53005872"
    },
    {
        "content": "",
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_cf5a5621fea7411bae7c702dd84f3236",
                "function": {
                    "name": "Translation",
                    "arguments": "{}"
                },
                "type": "function"
            }
        ]
    },
    {
        "content": "Ang 4 x 4 ay katumbas ng 16.\n\nPaliwanag sa Filipino:\nAng pag-multiply ng 4 sa 4 ay nangangahulugang ipinadadagdag mo ang bilang na 4 ng apat na beses (4 + 4 + 4 + 4), na nagreresulta sa sagot na 16.",
        "role": "tool",
        "tool_call_id": "call_cf5a5621fea7411bae7c702dd84f3236"
    }
]
---
{
    "name": "GeneralChat",
    "args": {},
    "usages": [
        {
            "name": "$tool",
            "model": "gpt-4.1",
            "usage": {
                "input_tokens": 315,
                "output_tokens": 49,
                "total_tokens": 364,
                "input_token_details": {
                    "audio": 0,
                    "cache_read": 0
                },
                "output_token_details": {
                    "audio": 0,
                    "reasoning": 0
                }
            }
        }
    ],
    "actions": [
        {
            "name": "MathProblem",
            "args": {
                "answer": "4 x 4 = 16"
            },
            "usages": [],
            "actions": []
        },
        {
            "name": "Translation",
            "args": {},
            "usages": [
                {
                    "name": null,
                    "model": "gpt-4.1",
                    "usage": {
                        "input_tokens": 117,
                        "output_tokens": 75,
                        "total_tokens": 192,
                        "input_token_details": {
                            "audio": 0,
                            "cache_read": 0
                        },
                        "output_token_details": {
                            "audio": 0,
                            "reasoning": 0
                        }
                    }
                }
            ],
            "actions": []
        }
    ]
}
```

</details>

---

## 🔄 Core Process

![Action Life Cycle](docs/action-life-cycle.png "Action Life Cycle")

### **Understanding the Action Life Cycle**

Every Action has **five core phases**: pre-process, children selection, children execution, fallback, and post-process.

#### 🎬 **Pre-Process: Preparation Phase**

- **Purpose**: Recommended for "preparation" before executing your next intent detection
- **Simple Actions**: If your action only needs one dedicated process, you can declare only pre-process and end the flow—this acts as the full execution
- **Nested Intent Detection**: Ideal for setup before processing nested intents

#### 🎯 **Children Selection: Intent Detection**

- **Purpose**: Processes which child intents to be executed next
- **Customizable**: You can override this and use your own selection method
- **Direct Control**: You can even override it by just returning your preferred child actions
- **Default Behavior**: Uses LLM tool call results to determine next actions

#### 🚀 **Children Execution: Action Processing**

- **Execution Order**: By default, executes tool call results in the order the LLM returns them
- **Concurrency Support**: Children can be annotated as concurrent (Thread or Task)
- **Wait Behavior**: By nature, waits for completion before continuing to post-process
- **Override Flexibility**: You can run them in separate threads without waiting if necessary
- **Recursive Processing**: Every child action executes their own complete life cycle

#### 🔧 **Fallback: Optional Response Handling**

- **Purpose**: Provides a graceful response mechanism when child actions are defined but none are selected by the LLM
- **Use Case**: Essential for maintaining conversation flow in scenarios like user requests that don't match any available child intents, or when the LLM needs to respond conversationally rather than execute a specific action
- **Tool Choice Behavior**:
  - **Default**: Tool choice is set to "required" (must select a child action)
  - **With Fallback**: Tool choice is set to "auto" (allows string responses)
- **Flexibility**: When no suitable child actions are detected, the tool call can return a string message to use as the response

#### 🏁 **Post-Process: Consolidation Phase**

- **Purpose**: Recommended for cleanup, consolidation, or termination
- **Response Merging**: Use this to consolidate responses from each child
- **Final Processing**: Perfect for generating merged or transformed outputs

### **Real-World Example**

Consider an AI Agent that supports two intents: **TellingJoke** & **TellingStory**, where **TellingStory** has child intents **HorrorStory** and **ComedyStory**:

```
YouAIAgent(Action):
├── TellingJoke(Action)
│   └── pre-process: generate joke
├── TellingStory(Action)
│   ├── HorrorStory(Action)
│   │   └── pre-process: generate horror story
│   └── ComedyStory(Action)
│       └── pre-process: generate comedy story
└── post-process: consolidate responses and generate merged story
```

#### **Flow Example**: _"Tell me a horror story and add a little joke on it"_

1. **TellingStory** processes → **HorrorStory** generates horror story
2. **TellingJoke** generates joke
3. **Post-process** consolidates both responses and generates a new merged story

This deterministic flow ensures predictable behavior while maintaining flexibility for complex nested intent processing and real-time decision making.

## 🎯 **Action High Level**

### **Life Cycle**

The Action Life Cycle above shows how Pybotchi processes intent through deterministic flows.

#### 🎨 **Intent-Based Design**

- **`Action`** declaration is similar to graph declaration
- You can scan through action flow **real time**—no need to generate graphs or read full declarations
- Actions are declared in **descriptive manner**
- Actions are considered **Intent** with support for categorizing and nested Intent:

  ```
  StoryTelling
  ├── Horror
  │   ├── Monsters
  │   └── Ghosts
  ├── Comedy
  │   ├── Fiction
  │   └── NonFiction
  └── Romance
      ├── HappyEnding
      └── TragicEnding

  MathProblem
  ├── Algebra
  └── Trigonometry
  ```

#### 🪶 **Lightweight & Flexible**

- **Ultra-lightweight**: only 2 classes working together—**`Action`** and **`Context`**
- Both classes are **completely overridable**
- **`Not required`** - since we're just abstracting agent execution, this is a tool that can be replaced with any other approach/framework

---

## 📚 Examples

Explore these example files to see Pybotchi in action:

#### 🚀 **Getting Started**

- [`examples/tiny.py`](examples/tiny.py) - Minimal implementation
- [`examples/full_spec.py`](examples/full_spec.py) - Full specs with descriptions

#### 🔄 **Flow Control**

- [`examples/sequential_combination.py`](examples/sequential_combination.py) - Tool call can call multiple actions in single invocation. This will run the actions in sequential manner
- [`examples/sequential_iteration.py`](examples/sequential_iteration.py) - Allowing iteration of own child actions while also supporting sequential combination or concurrent combination
- [`examples/nested_combination.py`](examples/nested_combination.py) - Nested structure that utilize inheritance and overrides

#### ⚡ **Concurrency**

- [`examples/concurrent_combination.py`](examples/concurrent_combination.py) - Tool call can call multiple actions in single invocation. This will execute the actions concurrently
- [`examples/concurrent_threading_combination.py`](examples/concurrent_threading_combination.py) - Same with concurrent_combination but it will be on different thread

#### 🌐 **Real-World Applications**

- [`examples/interactive_agent.py`](examples/interactive_agent.py) - Real-time client communication utilizing websocket
- [`examples/jira_agent.py`](examples/jira_agent.py) - Action connected to mcp-atlassian server. Action is the MCP Client
- [`examples/agent_with_mcp.py`](examples/agent_with_mcp.py) - This is for hosting Action to be as tool in of mcp server

**📖 More documentation coming soon...**
