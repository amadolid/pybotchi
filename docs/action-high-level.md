# **`Action High Level`**

## **Life Cycle**

![Action Life Cycle](action-life-cycle.png "Life Cycle")

## **Key Features**

- `Agent` is based from `Action`
- `Action` can be a `Agent`
- `Agent` can have zero (expecting to have at least pre or post process), one or multiple child agents/actions
- `Agent` can be dynamically generated in runtime. Requires existing actions to be attached to the generated `Agent`
- `Action` can open up undeclared branch/flow to run different `Agent/Action` regardless if it's async or not
- `Action` concurrency control is just bool flag `__concurrent__`
- every process have access to `context` (user_id, session_id, chat histories, memory, persona, socket, etc)
- every process can do anything including calling other frameworks like langgraph, crewai, swarm, gemini's alternative, etc
- `context` are just runtime data holder, any data that's needed in the flow can be saved here
- `Action` declaration is similar to graph declaration.
  - you can scan through action flow real time. No need to generate the graph or read the full declaration to understand
  - Actions are almost declared in descriptive manner
  - Actions are considered Intent. We support categorizing Intentand nested Intent. **Ex:**
    - StoryTelling
      - Horror
        - Monsters
        - Ghosts
      - Comedy
        - Fiction
        - NonFiction
      - Romance
        - HappyEnding
        - TragicEnding
    - MathProblem
      - Algebra
      - Trigonometry
- Very lite-weight, in terms of the agent execution, we only have 2 class working together `Action` and `Context` while also both of these are overridable
- **`Not required`** - since we are just abstracting agent execution, this is just a tool and can be replaced with any other approach/framework
- Have ordered action flow execution and usage preview
