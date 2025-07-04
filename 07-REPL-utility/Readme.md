# **REPL Utility**

## **What Is the REPL Utility?**

The SDK’s REPL (Read–Eval–Print Loop) utility, exposed as the run_demo_loop function, is a simple command-line interface for interactive prototyping and manual debugging of your agents. Rather than writing a full application around your agent, you can drop into a loop, type prompts, see results in real time (with streaming), and refine your instructions or tools on the fly.

## **Key Features:**

1. **Conversation State:** Automatically preserves the entire message history between turns.

2. **Streaming by Default:** Text appears token-by-token as the LLM generates it, giving you a “live typing” effect.

3. **Easy Exit:** Type quit, exit, or press Ctrl-D to leave the loop cleanly.

4. **Minimal Setup:** One function call—no boilerplate UI or I/O handling required.

## **How to Invoke run_demo_loop:**

The REPL lives in agents.repl.run_demo_loop. Here’s the minimal async example from the docs:

```python
import asyncio
from agents import Agent, run_demo_loop

async def main() -> None:
    # 1. Define a simple agent
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant."
    )

    # 2. Launch the interactive loop
    await run_demo_loop(agent)

if __name__ == "__main__":
    # Boot up the asyncio event loop
    asyncio.run(main())
```

By default, each turn’s output will stream as it’s generated To quit, simply type exit or press Ctrl-D.

## **Customizing the REPL:**

### **Disabling Streaming:**

If you prefer to see each complete reply at once rather than token by token:

```py
import asyncio
from agents import Agent, run_demo_loop

async def main() -> None:
    agent = Agent(name="Assistant", instructions="You are concise.")
    # Disable streaming: the REPL will wait for the full reply
    await run_demo_loop(agent, stream=False)

if __name__ == "__main__":
    asyncio.run(main())
```

### **Preloading Tools:**

Your agent can include any number of @function_tool-decorated Python functions. The loop will automatically prompt the agent to use them as needed:

```python
import asyncio
from agents import Agent, run_demo_loop, function_tool

@function_tool
def add(a: int, b: int) -> int:
    return a + b

async def main() -> None:
    agent = Agent(
        name="CalculatorAgent",
        instructions="Use the add tool when asked to add numbers.",
        tools=[add]
    )
    await run_demo_loop(agent)

if __name__ == "__main__":
    asyncio.run(main())
```

## **Under the Hood:**

Inside agents/repl.py, run_demo_loop roughly:

1. Keeps track of a list of message dicts ({"role": ..., "content": ...}).

2. Prompts the user for input in a while True loop.

3. Invokes either Runner.run_streamed(...) (if stream=True) or Runner.run(...).

4. Iterates over stream_events() when streaming:

   - Prints each token chunk as it arrives.
   - Flags tool calls, outputs, and agent handoffs with brief markers.

5. Appends the agent’s final message or tool output back into the history.

6. Repeats until the user types exit/quit or sends EOF.
