# **Running Agents:**

### 1. Definition:

In the Agents SDK, you never invoke an LLM directly—instead, you define one or more `Agent` objects (each with instructions, a model, optional tools, etc.) and then use the `Runner` class to execute that agent. The `Runner` manages the entire lifecycle: sending messages to the model, handling tool calls, performing handoffs, and finally returning a result.

### 2. **Methods of Runner:**

There are three primary methods on `Runner` for running an agent:

1. **`Runner.run()`** (asynchronous)
2. **`Runner.run_sync()`** (synchronous wrapper around `run()`)
3. **`Runner.run_streamed()`** (asynchronous streaming mode, returning partial updates)

**2.1. `Runner.run()` (Asynchronous):**

```python
from agents import Agent, Runner

async def main():
    # 1. Define a simple agent with just instructions and a model
    agent= Agent(
        name="Assistant",
        instructions="You are a helpful assistant."
    )

    # 2. Run the agent asynchronously with a user prompt
    result = await Runner.run(
        agent,
        "Write a haiku about recursion in programming."
    )

    # 3. Once complete, inspect the final_output
    print(result.final_output)
    # Example output:
    #   Code within the code,
    #   Functions calling themselves,
    #   Infinite loop’s dance.
```

- **What it returns:** A `RunResult` object that contains:
  - `final_output`: The final text or structured output from the last agent in the loop.
  - `messages`: Full list of request/response exchanges (LLM messages + tool calls).
  - `tool_calls`: List of all tools invoked, their inputs, and their outputs.
  - `handoffs`: Any handoff events where one agent passed control to another.
  - Other metadata (timestamps, IDs, etc.)

**2.2.** `Runner.run_sync()` (Synchronous):

```python
from agents import Agent, Runner

# Exactly the same steps as .run(), but synchronous.
assistant = Agent(
    name="Assistant",
    instructions="You are a helpful assistant."
)

result_sync = Runner.run_sync(
    starting_agent=assistant,
    input="Explain quantum computing in simple terms."
)
print(result_sync.final_output)
```

- Under the hood, `run_sync` simply calls `asyncio.get_event_loop().run_until_complete(Runner.run(...))`.
- **Use this** when you don’t want to manage `async/await` yourself (e.g., simple scripts or command-line tools).

**2.3.** `Runner.run_streamed()` (Asynchronous Streaming):

```python
from agents import Agent, Runner

async def main_stream():
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant."
    )

    # Request streaming mode
    run_streamed = Runner.run_streamed(
        starting_agent=agent,
        input="Write a step-by-step guide for baking a loaf of bread."
    )

    # run_streamed is a RunResultStreaming
    async for event in run_streamed.stream_events():
        # event.name could be "message_output_created", "tool_called", "tool_output", etc.
        # event.item carries the payload (a token, a tool input or output, etc.)
        print(f"[{event.name}] {event.item}")
```

- **What it returns:** A `RunResultStreaming` object, which you can iterate over to receive `StreamEvent` objects in real time.
- **Why use it:**
  - Show “typing…” effects in a chat UI.
  - Surface intermediate tool calls or handoff events as soon as they happen.
  - Provide progress updates for long-running or multi-step agent flows.

---

### 3. **The Agent Loop:**

Regardless of which Runner method you choose, the SDK runs a single loop under the hood. Here is how that loop works, step by step:

1. **Initial Invocation**

   - You pass a starting_agent and some input to run() / run_sync() / run_streamed().

   - The input can be a simple string (treated as a “user” message) or a list of low-level response items (for advanced use).

2. **LLM Call for the Current Agent**

   - The SDK packages the instructions (system prompt), plus any accumulated messages or tool outputs, and sends them to the model you configured for that agent.

3. **LLM Output**

   - Once the model replies, one of three things happens:

   **a. Final Output Detected**

   - If the agent has an output_type (e.g., a Pydantic schema) and the model’s text matches that schema, or if the agent has no output_type but simply returns text with no pending tools/handoffs, the loop terminates.

   - You receive a RunResult (or, in streaming mode, the final event that indicates completion).

   **b. Tool Calls Generated**

   - If the LLM’s response indicates “I want to call tool X with inputs Y,” the SDK extracts that intent, invokes the Python function (or external API) you registered as a @function_tool, captures its output, and re-runs the loop with the tool output appended as a new “agent response.”

   **c. Handoff Requested**

   - If the LLM signals “handoff to Agent B,” the SDK changes the “current agent” to Agent B, resets the input to whatever the LLM provided for Agent B, and re-runs the loop with the new agent context.

4. **Repeat Until Termination**

   - Steps 2–3 repeat until you get a final output or an exception (e.g., max turns exceeded or a guardrail is tripped).

5. **Max Turns Check**

   - If the number of iterations (turns) surpasses max_turns (default 10), the SDK raises a MaxTurnsExceeded exception. You can override max_turns via the run_config (covered below).

```
Visually:

┌─────────────┐
│ Start agent │ <— you supply starting_agent & user input
└──────┬──────┘
↓
┌───────────────────────────────┐
│ Call LLM for current agent │
└──────┬────────────────────────┘
↓
┌────────────────────────────────────────────────┐
│ LLM output: │
│ - If final_output → exit loop │
│ - If tool_call → run tool, append result, loop│
│ - If handoff → switch agent, loop │
└────────────────────────────────────────────────┘
↓
(loops) 3. Streaming
```

---

### 4. **Streaming:**

Streaming mode is an extension of “Running Agents,” where instead of waiting for the entire workflow to finish, you subscribe to incremental updates. This can include:

- Partial text tokens from the LLM (“I am…”, “I am a model…”, etc.).
- Tool-called events as soon as they are dispatched.
- Tool outputs immediately when available.
- Handoff notifications right when one agent delegates to another.

### **3.1. How to Stream**

```python
from agents import Agent, Runner

async def run_with_streaming():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant.")

    # Start streaming run
    streaming_result = Runner.run_streamed(
        starting_agent=agent,
        input="Plan my day with exercise, study, and lunch."
    )

    async for event in streaming_result.stream_events():
        # event.name: string like "message_output_created", "tool_called", etc.
        # event.item: the actual payload (text chunk, tool name, or tool result)
        if event.name == "message_output_created":
            # The LLM just generated a new token or message piece
            token_text = event.item.content  # depends on API version
            print(token_text, end="", flush=True)
        elif event.name == "tool_called":
            print("\n[Tool Called]:", event.item.tool_name)
        elif event.name == "tool_output":
            print("[Tool Output]:", event.item)  # the tool's return value
        elif event.name == "handoff_requested":
            print("[Handoff to]", event.item.next_agent_name)
```

- **`run_streamed()`** returns immediately with a `RunResultStreaming`.
- You then iterate over `stream_events()`, handling each `StreamEvent` as it arrives.
- Once the agent finally produces a “final output,” you’ll receive a terminal event indicating completion (e.g., a “final_output” type event).

### **3.2. Why Use Streaming**

- **Better UX for Chat UIs:** Show the user “typing…” so they don’t stare at a blank screen.
- **Progress Feedback:** If your agent is invoking a slow tool (e.g., a long HTTP request), you can show intermediate states (“Searching…”, “Found result #1…”, etc.).
- **Debug & Logging:** Record every micro-step (tool calls, handoffs) in real time to your logs or monitoring dashboards.

### 5. **RunConfig:**

## 4. RunConfig

Sometimes you need to adjust settings on a per-run basis (rather than at agent creation time). That’s what `RunConfig` is for. You bundle up things like:

- **`model` / `model_provider`**: Swap out which LLM or LLM client to use for this specific invocation.
- **`tracing_disabled`**: Turn tracing on or off for a single run.
- **`tool_choice`**: Force or prohibit certain tool usage (covered separately).
- **`max_tokens`, `temperature`, etc.**: Override any model tuning parameters temporarily.

### 4.1. Example: Overriding the Model

```python
from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI

# Suppose you normally use GPT-4, but for this particular question you want GPT-3.5.
client = AsyncOpenAI(api_key="YOUR_KEY")
gpt35_model = OpenAIChatCompletionsModel(model="gpt-3.5-turbo", openai_client=client)
run_cfg = RunConfig(model=gpt35_model, model_provider=client)

my_agent = Agent(name="Assistant", instructions="You are helpful.")

# This run will use GPT-3.5 instead of the default model set on my_agent.
result = Runner.run_sync(
    starting_agent=my_agent,
    input="What is the history of the Eiffel Tower?",
    run_config=run_cfg
)
print(result.final_output)
```

- **When to use RunConfig:**

  - Experimenting with different models or parameters.
  - Overriding tracing behavior for troubleshooting (e.g., `tracing_disabled=True`).
  - Temporarily forcing or disabling certain tools (via `tool_choice`).

---

### 6. **Conversations / Chat Threads:**

By default, when you pass a **string** to `Runner.run()` or `run_sync()`, the SDK treats that as a single “user” message with no prior history. Internally, each turn is appended to a growing list of “messages” that represent the conversation between user, agent (LLM), tools, and sub-agents.

#### **6.1. Maintaining a Chat Thread Manually**

If you want to preserve conversation history across multiple calls to `Runner.run_sync()`, you can:

1. Extract `RunResult.messages` from the first run (this is a list of items: user prompt, any tool calls, agent responses).
2. On subsequent runs, pass that same list plus your new user question.

```python
async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.")

    with trace(workflow_name="Conversation", group_id=thread_id):
        # First turn
        result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
        print(result.final_output)
        # San Francisco

        # Second turn
        new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
        result = await Runner.run(agent, new_input)
        print(result.final_output)
        # California
```

- **Why do this?**

  - Keeps context across multiple calls without rebuilding a single “mega-prompt.”
  - The SDK handles returning model tokens, tool outputs, and handoffs in that `messages` list.

#### **6.2. Letting the Agent Manage the Thread**

If you’re using a single `.run()` call for a multi-turn conversation, internal agent logic can automatically chain without you merging `messages`. For example, if the agent’s instructions prompt it to “ask a follow-up question” before answering, it will automatically loop, ask the question (LLM call), incorporate your response (tool or user input), and so on—until it’s ready to terminate with final output.

---

### 7. **Exceptions:**

**7.1 AgentsException:**

- **What it is:** The base class for all exceptions in the Agents SDK. You generally won’t raise this directly, but every other exception in the SDK inherits from it.
- **Usage:** You can catch it to handle “any agent-related error.”

  ```python
  from agents.exceptions import AgentsException

  try:
      # …some agent run or setup…
      result = Runner.run_sync(some_agent, "Hello")
  except AgentsException as e:
      print("An agents-SDK error occurred:", str(e))
  ```

**7.2 MaxTurnsExceeded:**

- **What it is:** Raised when an agent’s internal loop exceeds the allowed number of “turns” (default is 10) without producing a final output.
- **Why it happens:** If the agent keeps calling tools or handing off endlessly and never returns a terminating answer, the SDK aborts to prevent an infinite loop.
- **Minimal Example:**

  ```python
  from agents import Agent, Runner
  from agents.exceptions import MaxTurnsExceeded

  # Suppose this agent’s instructions cause it to ping itself indefinitely:
  loop_agent = Agent(name="LoopBot", instructions="Ask me anything to continue looping.")

  try:
      Runner.run_sync(loop_agent, "Start the loop")
  except MaxTurnsExceeded as e:
      print("Error: Agent exceeded maximum allowed turns.")
  ```

**7.3 ModelBehaviorError:**

- **What it is:** Raised when the model does something completely unexpected—e.g., it tries to call a tool name that doesn’t exist, or it returns malformed JSON when the agent was expecting valid JSON.
- **Why it happens:** The SDK parses the LLM’s output to detect tool calls or validate schemas. If that parsing fails (invalid tool name, bad JSON, etc.), a `ModelBehaviorError` is thrown.
- **Minimal Example:**

  ```python
  from agents import Agent, Runner, function_tool
  from agents.exceptions import ModelBehaviorError

  @function_tool
  def echo(x: str) -> str:
      return x

  # Agent expects only the "echo" tool but the model might attempt something else
  faulty_agent = Agent(
      name="FaultyModelAgent",
      instructions="Call the non_existent_tool on input.",
      model="gpt-4",
      tools=[echo],
  )

  try:
      Runner.run_sync(faulty_agent, "Invoke non_existent_tool with 'hello'")
  except ModelBehaviorError as e:
      print("Model behaved unexpectedly:", str(e))
  ```

**7.4 UserError:**

- **What it is:** Raised when the user of the SDK makes a mistake in how they configure or call the Agents API—e.g., passing invalid arguments to functions or mixing incompatible types.
- **Why it happens:** If you call an SDK method with bad parameters (e.g. missing required fields, wrong data types), the SDK will throw `UserError`.
- **Minimal Example:**

  ```python
  from agents import Agent
  from agents.exceptions import UserError

  try:
      # Missing required 'instructions' argument
      invalid_agent = Agent(name="NoInstructionsAgent", model="gpt-4")
  except UserError as e:
      print("UserError caught:", str(e))
  ```

**7.5 InputGuardrailTripwireTriggered:**

- **What it is:** Raised when an **input guardrail** (a pre-defined validation or policy check) detects a violation in the user’s input before it reaches the model.
- **Why it happens:** You’ve registered a guardrail that, for example, disallows profanity or requires certain fields. If the incoming message trips that guardrail, the SDK throws this exception instead of calling the LLM.
- **Minimal Example:**

  ```python
  from agents import Agent, Runner
  from agents.guardrails import InputGuardrail, InputGuardrailResult
  from agents.exceptions import InputGuardrailTripwireTriggered

  # A trivial guardrail that rejects any input containing “forbidden”
  class NoForbiddenWords(InputGuardrail):
      def validate(self, text: str) -> InputGuardrailResult:
          if "forbidden" in text:
              return InputGuardrailResult(self, passed=False, message="Contains forbidden word")
          return InputGuardrailResult(self, passed=True, message="OK")

  guarded_agent = Agent(
      name="GuardedAgent",
      instructions="You are a friendly assistant.",
      model="gpt-4",
      guardrails=[NoForbiddenWords()],
  )

  try:
      Runner.run_sync(guarded_agent, "This input contains the word forbidden.")
  except InputGuardrailTripwireTriggered as e:
      print("Input guardrail triggered:", e.guardrail_result.message)
  ```

**7.6 OutputGuardrailTripwireTriggered:**

- **What it is:** Raised when an **output guardrail** (a post-generation validation or policy) detects a violation in the model’s response before returning it.
- **Why it happens:** You’ve registered a guardrail that, for example, enforces a JSON schema. If the LLM’s generated text fails to match that schema, the SDK throws this exception.
- **Minimal Example:**

  ```python
  from agents import Agent, Runner
  from agents.guardrails import JSONSchemaGuardrail
  from agents.exceptions import OutputGuardrailTripwireTriggered

  schema = {
      "type": "object",
      "properties": {"answer": {"type": "string"}},
      "required": ["answer"]
  }

  json_guard = JSONSchemaGuardrail(schema=schema)

  json_agent = Agent(
      name="JSONAgent",
      instructions="Respond with valid JSON {\"answer\": \"...\"}.",
      model="gpt-4",
      guardrails=[json_guard],
  )

  try:
      Runner.run_sync(json_agent, "Say something not in JSON format.")
  except OutputGuardrailTripwireTriggered as e:
      print("Output guardrail triggered:", e.guardrail_result.message)
  ```

---
