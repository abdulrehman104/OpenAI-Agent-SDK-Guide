



## 6. Exceptions

When running an agent, two main exceptions can be raised:

### 6.1. `MaxTurnsExceeded`

* **What it means:** The agent loop has iterated more times than `max_turns`.
* **Default `max_turns`:** 10
* **When it happens:** For example, if an agent keeps calling tools or handing off to sub-agents without ever producing a final output, after 10 turns the SDK will abort to prevent infinite loops.

```python
from agents import Agent, Runner, MaxTurnsExceeded

agent = Agent(name="LoopBot", instructions="Ask me a question to keep the loop going.")

try:
    Runner.run_sync(agent, "Start the loop")
except MaxTurnsExceeded as e:
    print("Agent did not finish within the allowed turns.")
```

* **How to fix or adjust:**

  * Ensure your agent’s instructions include a termination condition.
  * Increase `max_turns` via `run_config=RunConfig(max_turns=20)` if you know you need more iterations.

### 6.2. `GuardrailTripwireTriggered`

* **What it means:** One of your agent’s guardrails (input or output validation checks) fired.
* **Why it matters:** Guardrails allow you to enforce policy rules—e.g., “do not produce PII,” “reject disallowed content,” or “require a valid JSON schema.”
* **Example scenario:** If your guardrail says “output must be valid JSON as per my Pydantic model” but the LLM returns invalid JSON, the SDK raises this exception.

```python
from agents import Agent, Runner, GuardrailTripwireTriggered
from agents.guardrails import Guardrail, JSONSchemaGuardrail

# Suppose we want to force JSON output matching this schema:
schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"}
    },
    "required": ["answer", "confidence"],
}

json_guard = JSONSchemaGuardrail(schema=schema)

agent = Agent(
    name="JSONBot",
    instructions="Reply in JSON with fields 'answer' and 'confidence'.",
    model="gpt-4",
    guardrails=[json_guard]
)

try:
    Runner.run_sync(agent, "What is 2 + 2?")
except GuardrailTripwireTriggered as e:
    print("Guardrail failed (probably invalid JSON).")
```

* **How to handle:**

  * Adjust your instructions or guardrail schema so the LLM can comply.
  * Catch the exception and provide fallback behavior (e.g., re-ask the question with clearer instructions).

---

## Putting It All Together: A Full Example

Below is a self-contained example that demonstrates:

1. **Defining an agent with a tool**
2. **Running it asynchronously**
3. **Using streaming**
4. **Applying a custom `RunConfig`**
5. **Preserving conversation history manually**
6. **Catching exceptions**

```python
import asyncio
from agents import (
    Agent,
    Runner,
    RunConfig,
    function_tool,
    MaxTurnsExceeded,
    GuardrailTripwireTriggered,
)
from agents.guardrails import JSONSchemaGuardrail
from agents.model_settings import ModelSettings

# --- 1. Define a simple tool ---
@function_tool
def add_numbers(a: int, b: int) -> int:
    return a + b

# --- 2. Define a guardrail for JSON output ---
schema = {
    "type": "object",
    "properties": {
        "sum": {"type": "number"}
    },
    "required": ["sum"],
}
json_guard = JSONSchemaGuardrail(schema=schema)

# --- 3. Create an agent that can call add_numbers, 
#     and must produce JSON with a "sum" field. ---
model_settings = ModelSettings(temperature=0.0)
calc_agent = Agent(
    name="CalculatorAgent",
    instructions="Use the add_numbers tool, then output JSON like {\"sum\": <result>}.",
    model="gpt-4",
    model_settings=model_settings,
    tools=[add_numbers],
    guardrails=[json_guard]
)

async def main():
    # --- 4. Run streaming with a custom RunConfig (max_turns=5) ---
    run_cfg = RunConfig(max_turns=5)
    streamed = Runner.run_streamed(
        starting_agent=calc_agent,
        input="What is 6 + 7?",
        run_config=run_cfg
    )

    print("---- Streaming Output ----")
    async for e in streamed.stream_events():
        if e.name == "message_output_created":
            # Print each text token from the LLM
            print(e.item.content, end="", flush=True)
        elif e.name == "tool_called":
            print(f"\n[Tool Called: {e.item.tool_name}]")
        elif e.name == "tool_output":
            print(f"\n[Tool Output: {e.item}]")
        elif e.name == "handoff_requested":
            print(f"\n[Handoff to: {e.item.next_agent_name}]")

    print("\n---- Final Result ----")

    # --- 5. Now run synchronously, preserving chat history from above ---
    # (In practice, you would collect previous messages from RunResult or RunResultStreaming)
    # Here we simulate fresh conversation:
    try:
        res1 = Runner.run_sync(
            starting_agent=calc_agent,
            input="What is 8 + 15?",
            run_config=RunConfig(max_turns=3)
        )
        print("Result 1:", res1.final_output)

        # 6. Manually preserve chat history:
        thread = res1.messages + ["And then, what is 10 + 5?"]
        res2 = Runner.run_sync(
            starting_agent=calc_agent,
            input=thread,
            run_config=RunConfig(max_turns=3)
        )
        print("Result 2:", res2.final_output)

    except MaxTurnsExceeded:
        print("Error: Agent took too many steps.")
    except GuardrailTripwireTriggered:
        print("Error: Guardrail validation failed.")

# Kick off the async example
asyncio.run(main())
```

**What this demo does:**

1. Registers a Python function `add_numbers(a, b) → a + b` as a tool.
2. Creates `CalculatorAgent` that:

   * Uses GPT-4 with low temperature (deterministic).
   * Has a JSON guardrail forcing output to match `{"sum": <number>}`.
   * Can invoke `add_numbers`.
3. First, runs the agent in **streaming mode** for “6 + 7,” printing tokens, tool calls, and tool outputs as they happen.
4. Then, runs it synchronously for “8 + 15,” capturing `res1.messages`.
5. Demonstrates carrying conversation history into a second run with “10 + 5.”
6. Catches both `MaxTurnsExceeded` and `GuardrailTripwireTriggered` exceptions to show how to handle failure cases.

---

### Summary of Key Concepts

* **`Runner.run()` / `run_sync()` / `run_streamed()`**: Three ways to execute agents, depending on whether you need sync vs. async vs. partial updates.
* **Agent Loop**: Internally, the SDK repeatedly calls the LLM, checks for final output, tool calls, or handoffs, and loops until termination or an exception.
* **Streaming**: Subscribe to `StreamEvent`s (LLM tokens, tool calls, tool outputs, handoffs) for real-time feedback.
* **RunConfig**: Override settings (model, temperature, max\_turns, tool\_choice, tracing) on a per-run basis.
* **Conversation/Chat Threads**: Preserve `RunResult.messages` to maintain context across multiple calls.
* **Exceptions**:

  * `MaxTurnsExceeded`: Agent loop took too many turns.
  * `GuardrailTripwireTriggered`: Guardrail checks failed (input or output validation).

With these tools and concepts in hand, you have everything you need to design robust, multi-step AI workflows—whether you’re building a simple chat assistant or a multi-agent orchestration that calls external APIs, enforces strict policies, and streams progress updates in real time.
