# 🤖 Pybotchi

> _A deterministic, intent-based AI agent builder with no restrictions—supports any framework and prioritizes human-reasoning approach._

---

## 🎯 Core Philosophy

**Humans should handle the reasoning. AI should detect intent and translate natural language into processable data.**

LLMs excel at **intent detection and translation**. Pybotchi leverages this strength while prioritizing the human way of declaring planning and reasoning through **tool call chaining**—where AI becomes the perfect interpreter between human intent and computational action.

---

## ⚡ Core Architecture

**Nested Intent-Based Supervisor Agent Architecture** with only **3 core classes**:

- **`Action`** - Describes the intent and execution logic
- **`Context`** - Holds prompts, metadata, and execution state
- **`LLM`** - LLM client instance holder

---

## 🚀 Quick Start

### **Setup LLM**

```python
from langchain_openai import ChatOpenAI
from pybotchi import LLM

LLM.add(base=ChatOpenAI(...))
```

### **Simple Agent**

```python
from pybotchi import Action, ActionReturn, Context

class Translation(Action):
    """Translate to specified language."""

    async def pre(self, context: Context) -> ActionReturn:
        message = await context.llm.ainvoke(context.prompts)
        await context.add_response(self, message.text())
        return ActionReturn.GO
```

### **Agent with Fields**

```python
class MathProblem(Action):
    """Solve math problems."""

    answer: str

    async def pre(self, context: Context) -> ActionReturn:
        await context.add_response(self, self.answer)
        return ActionReturn.END
```

### **Multi-Agent Declaration**

```python
class MultiAgent(Action):
    """AI Assistant for solving math problems and translation."""

    class SolveMath(MathProblem):
        pass

    class Translate(Translation):
        pass
```

### **Execution**

```python
import asyncio

async def test():
    context = Context(
        prompts=[
            {"role": "system", "content": "You're an AI that can solve math problems and translate requests."},
            {"role": "user", "content": "4 x 4 and explain in Filipino"}
        ],
    )
    action, result = await context.start(MultiAgent)
    print(context.prompts[-1]["content"])

asyncio.run(test())
```

**Result:** _Ang 4 x 4 ay katumbas ng 16._

_Paliwanag sa Filipino:_
_Ang pag-multiply ng 4 sa 4 ay nangangahulugang ipinadadagdag mo ang bilang na 4 ng apat na beses (4 + 4 + 4 + 4), na nagreresulta sa sagot na 16._

### **Graph**

```python
from pybotchi import graph

async def print_mermaid_graph():
    print(await graph(MultiAgent))
```

**Result:**

```
flowchart TD
__main__.MultiAgent.Translate[__main__.MultiAgent.Translate]
__main__.MultiAgent[__main__.MultiAgent]
__main__.MultiAgent.SolveMath[__main__.MultiAgent.SolveMath]
__main__.MultiAgent --> __main__.MultiAgent.Translate
__main__.MultiAgent --> __main__.MultiAgent.SolveMath
```

![MultiAgent Graph](docs/mermaid.png)

---

## 🧩 Core Features

### **Everything is Overridable & Extendable**

```python
class CustomAgent(MultiAgent):
    SolveMath = None  # Remove action

    class NewAction(Action):  # Add new action
        pass

    class Translate(Translation):  # Override existing
        async def pre(self, context):
            # Custom translation logic
            pass
```

### **Sequential & Concurrent Execution**

- **Sequential**: Multiple agents execute in order
- **Concurrent**: Parallel execution using threads or tasks
- **Iteration**: Multiple executions via loops

### **MCP Integration**

- **As Server**: Mount agents to FastAPI as MCP endpoints
- **As Client**: Connect to MCP servers and integrate tools
- **Tool Override**: Customize or replace MCP tools

### **Flexible Lifecycle Control**

- **Pre-Process**: Setup and preparation
- **Children Selection**: Custom intent detection logic
- **Children Execution**: Sequential or concurrent processing
- **Fallback**: Graceful handling when no intent matches
- **Post-Process**: Response consolidation and cleanup

![Action Lifecycle](docs/action-life-cycle.png)

---

## 🎨 Key Benefits

- **🪶 Ultra-lightweight**: Only 3 core classes to master
- **🔧 Completely overridable**: Every component can be customized
- **🎯 Intent-focused**: Leverages AI's natural language strengths
- **⚡ Async-first**: Built for real-world web service integration
- **🔄 Deterministic**: Predictable flows make debugging simple
- **🌐 Framework-agnostic**: Works with any LLM framework
- **📊 Built-in tracking**: Automatic usage monitoring and metrics
- **🤝 Community-driven**: Modular agents maintained by different teams

---

## 🌟 Advanced Capabilities

### **Nested Agent Architecture**

```python
class ComplexAgent(Action):
    class StoryTelling(Action):
        class HorrorStory(Action):
            pass
        class ComedyStory(Action):
            pass

    class JokeTelling(Action):
        pass
```

### **Dynamic Agent Composition**

```python
# Add children dynamically
ComplexAgent.add_child(NewAction)
ComplexAgent.StoryTelling.add_child(SciFiStory)
```

---

## 🚀 Why Choose Pybotchi?

**Maximum flexibility, zero lock-in.** Build agents that combine human intelligence with AI precision. Perfect for teams that need:

- Modular, maintainable agent architectures
- Framework flexibility and migration capabilities
- Community-driven agent development
- Enterprise-grade customization and control
- Real-time interactive agent communication

**Ready to build smarter agents?** Start with the examples and join the community building the future of human-AI collaboration.

---

## 📚 Examples & Use Cases

Ready to dive deeper? Check out these practical examples:

### 🚀 **Getting Started**

- [`tiny.py`](https://github.com/amadolid/pybotchi/blob/master/examples/tiny.py) - Minimal implementation to get you started
- [`full_spec.py`](https://github.com/amadolid/pybotchi/blob/master/examples/full_spec.py) - Complete feature demonstration

### 🔄 **Flow Control**

- [`sequential_combination.py`](https://github.com/amadolid/pybotchi/blob/master/examples/sequential_combination.py) - Multiple actions in sequence
- [`sequential_iteration.py`](https://github.com/amadolid/pybotchi/blob/master/examples/sequential_iteration.py) - Iterative action execution
- [`nested_combination.py`](https://github.com/amadolid/pybotchi/blob/master/examples/nested_combination.py) - Complex nested structures

### ⚡ **Concurrency**

- [`concurrent_combination.py`](https://github.com/amadolid/pybotchi/blob/master/examples/concurrent_combination.py) - Parallel action execution
- [`concurrent_threading_combination.py`](https://github.com/amadolid/pybotchi/blob/master/examples/concurrent_threading_combination.py) - Multi-threaded processing

### 🌐 **Real-World Applications**

- [`interactive_agent.py`](https://github.com/amadolid/pybotchi/blob/master/examples/interactive_agent.py) - Real-time WebSocket communication
- [`jira_agent.py`](https://github.com/amadolid/pybotchi/blob/master/examples/jira_agent.py) - Integration with MCP Atlassian server
- [`agent_with_mcp.py`](https://github.com/amadolid/pybotchi/blob/master/examples/agent_with_mcp.py) - Hosting Actions as MCP tools

### ⚔️ **Framework Comparison (Get Weather)**

- [`Pybotchi`](https://github.com/amadolid/pybotchi/blob/master/examples/vs/pybotchi_approach.py)
- [`LangGraph`](https://github.com/amadolid/pybotchi/blob/master/examples/vs/langgraph_approach.py)
