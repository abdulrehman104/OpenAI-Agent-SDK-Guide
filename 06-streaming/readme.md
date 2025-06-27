# **Streaming:**

## **What is Streaming:**

Streaming is a way to receive incremental, real-time updates from an AI model or agent, rather than waiting for the entire response to finish before you see anything. As pieces of the output become available—tokens of text, tool results, or other events—they’re “streamed” to your application immediately.

## **Agent Streaming:**

**What it is:**
Streaming lets you observe an agent’s execution as it happens—tokens from the LLM, tool calls, tool results, handoffs, and agent switches—rather than waiting for the entire workflow to finish. It’s invaluable for:

**How it works:**
You call Runner.run_streamed(...) in the Agent SDK. The SDK emits a stream of events—token chunks, tool-call notifications, tool outputs, handoff requests, etc.

```python
from agents import Runner

# `agent` is your configured Agent instance
result: RunResultStreaming = Runner.run_streamed(agent, input="Please tell me 5 jokes.")
```

**What you see:** A mix of:

1. Token events (partial text replies)
2. Tool events (e.g. “Called get_weather with city=Tokyo”)
3. Tool results (e.g. “Weather is sunny”)
4. Handoff events (e.g. “Switching to FlightBookingAgent”)

## **Runner.run_streamed:**

Run a workflow starting at the given agent in streaming mode. The returned result object
contains a method you can use to stream semantic events as they are generated.
The agent will run in a loop until a final output is generated. The loop runs like so:

1. The agent is invoked with the given input.
2. If there is a final output (i.e. the agent produces something of type
   `agent.output_type`, the loop terminates.
3. If there's a handoff, we run the loop again, with the new agent.
4. Else, we run tool calls (if any), and re-run the loop.

In two cases, the agent may raise an exception:

1. If the max_turns is exceeded, a MaxTurnsExceeded exception is raised.
2. If a guardrail tripwire is triggered, a GuardrailTripwireTriggered exception is raised.

Note that only the first agent's input guardrails are run.
Args:

- starting_agent: The starting agent to run.
- input: The initial input to the agent. You can pass a single string for a user message,
  or a list of input items.
- context: The context to run the agent with.
- max_turns: The maximum number of turns to run the agent for. A turn is defined as one
  AI invocation (including any tool calls that might occur).
- hooks: An object that receives callbacks on various lifecycle events.
- run_config: Global settings for the entire agent run.
- previous_response_id: The ID of the previous response, if using OpenAI models via the
  Responses API, this allows you to skip passing in input from the previous turn.
- Returns: A result object that contains data about the run, as well as a method to stream events.

```python
def run_streamed(
    cls,
    starting_agent: Agent[TContext],
    input: str | list[TResponseInputItem],
    context: TContext | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    hooks: RunHooks[TContext] | None = None,
    run_config: RunConfig | None = None,
    previous_response_id: str | None = None,
) -> RunResultStreaming:
```

## **RunResultStreaming:**

**Definition**

- The object returned immediately by `Runner.run_streamed()`.
- Extends the normal RunResult with live streaming support.
- The result of an agent run in streaming mode. You can use the `stream_events` method to
  receive semantic events as they are generated.

**Purpose**

- Gives you access to both the final run data (final output, tool calls, guardrails, etc.) and a stream of intermediate events as they happen.

**Role on the Stage**

This is the live broadcast version of RunResultBase.

- Who listens? UIs or controllers that want updates as soon as they happen.
- What extra it adds?
  - A pointer to the current agent (useful if you switch between multiple agents).
  - A stream of events you can subscribe to via stream_events().
- When to use it? When you want to show progress in real-time—“Agent is thinking… Tool is running… Answer is here.”

**Inheritance**

```nginx
RunResultStreaming
└─ RunResultBase
```

**Example**

```py
from agents import Runner

# Kick off a streaming run
result: RunResultStreaming = Runner.run_streamed(agent, input="Calculate 2+2")
# You can still inspect final_output after the loop
```

## **StreamEvent:**

**Definition**

- Stream deltas for new items as they are generated. We're using the types from the OpenAI Responses API, so these are semantic events: each event has a `type` field that describes the type of the event, along with the data for that event.

**Purpose**

- To provide a single interface for subscribing to every kind of streaming update—whether it’s raw token deltas, high-level run items, or agent switches—so clients can handle them uniformly.

**Role on the Stage**

Acts as the umbrella type for any event you receive from:

- RawResponsesStreamEvent (token-level updates)
- RunItemStreamEvent (message/tool/handoff milestones)
- AgentUpdatedStreamEvent (agent-switch notifications)

Your streaming loop will simply iterate StreamEvent objects and dispatch based on their concrete class.

**Inheritance**

Not a class itself, but a union of three dataclasses defined in agents/stream_events.py:

- RawResponsesStreamEvent
- RunItemStreamEvent
- AgentUpdatedStreamEvent
  **Example**

```py
import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner
from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent, AgentUpdatedStreamEvent

async def stream_demo():
    agent = Agent(name="Streamer", instructions="Tell a story.")
    result = Runner.run_streamed(agent, input="Begin your story.")

    async for event in result.stream_events():
        # 1) Raw LLM token
        if isinstance(event, RawResponsesStreamEvent) and hasattr(event.data, "delta"):
            print(event.data.delta, end="", flush=True)

        # 2) Completed run item (message, tool call/output, etc.)
        elif isinstance(event, RunItemStreamEvent):
            print(f"\n[Step: {event.name}] -> {event.item}")

        # 3) Agent switch
        elif isinstance(event, AgentUpdatedStreamEvent):
            print(f"\n*** Now using agent: {event.new_agent.name} ***")

    # After streaming, full result still available
    print("\n\nFinal output:", result.final_output)

if __name__ == "__main__":
    asyncio.run(stream_demo())
```

## **RawResponsesStreamEvent:**

**Definition**

A RawResponsesStreamEvent is a dataclass representing one chunk of streaming output directly from the LLM (for example, a token or partial token delta).

**Purpose**

- `Expose low-level LLM streaming:` It mirrors the OpenAI ChatCompletion stream=True behavior inside the Agent SDK.

- Serve `“typing” UIs or real-time pipelines:` By forwarding each token or chunk as soon as it arrives, you can implement live-typing indicators, progressive display, or immediate downstream processing.

**Role on the Stage**

Think of RawResponsesStreamEvent as the play-by-play announcer for the model’s own text generation.

- Who listens? Your streaming loop or UI component that wants each piece of text as soon as it’s generated.
- What it announces? Every token (or token cluster) the LLM emits, along with any associated usage metrics.

**Inheritance**

- Not a subclass of any other class, but it is one variant in the StreamEvent union type:

  ```py
  StreamEvent = Union[
      RawResponsesStreamEvent,
      RunItemStreamEvent,
      AgentUpdatedStreamEvent,
  ]
  ```

- Defined in src/agents/stream_events.py as a standalone dataclass.
  openai.github.io

**core attributes**
| Attribute | Type | Description |
| --------- | ------------------------------- | -------------------------------------------------------------------- |
| `data` | `TResponseStreamEvent` | The raw chunk of data from the LLM stream (token delta). |
| `type` | `Literal["raw_response_event"]` | A constant string `"raw_response_event"` identifying the event type. |

**Example**

```py
import asyncio
from agents import Runner
from agents.stream_events import RawResponsesStreamEvent

async def live_chat(agent, prompt: str):
    # Start the streamed run
    result = await Runner.run_streamed(agent, input=prompt)

    # Iterate over StreamEvents as they arrive
    async for event in result.stream_events():
        if isinstance(event, RawResponsesStreamEvent):
            # `event.data` holds the raw token or chunk
            print(event.data.choices[0].delta.get("content", ""), end="", flush=True)

    # After streaming, you still have the complete result
    print("\nFinal answer:", result.final_output)

# Example usage:
# asyncio.run(live_chat(my_agent, "Tell me a story about a dragon."))
```

1. Start streaming with Runner.run_streamed(...).
2. Check for RawResponsesStreamEvent via isinstance.
3. Print each token/chunk as event.data.

## **RunItemStreamEvent:**

**Definition**

A RunItemStreamEvent is a streaming event emitted by the Agent SDK whenever a discrete “run item” finishes during a streamed agent execution. A “run item” can be:

- An LLM message output
- A tool invocation request
- A tool’s output
- A handoff request to another agent
- An internal reasoning snippet (if enabled)

It wraps the completed RunItem object so you can react to each logical step as soon as it finishes.

**Purpose**

- Surface Semantic Milestones

  - Rather than streaming raw tokens, this event tells you when each meaningful unit of work is done.

- Drive Step-By-Step UIs or Logs

  - You can update progress indicators, append completed tool results to a sidebar, or log each action in real time.

- Enable Fine-Grained Observability
  - Track exactly which tool was called when, and with what inputs, without waiting for the full run to complete.

**Role on the Stage**

- Announcer of Completed Steps

  - Acts as a clear “ding” that a particular sub-task or message has finished.

- Bridge Between Raw Tokens and Final Output

  - Sits between the low-level token stream and the final aggregated RunResult, giving you structured, digestible updates.

- Coordinator for Complex Flows
  - In multi-tool or multi-agent scenarios, it’s the signal to trigger UI updates, metric collection, or conditional branching based on a tool’s output.

**Inheritance**

```nginx
StreamEvent
└─ RunItemStreamEvent
```

- `StreamEvent:` Base class for all streaming events.
- `RunItemStreamEvent:` Specializes StreamEvent to carry a RunItem.

**Core Attributes**

| Attribute   | Type       | Description                                                              |
| ----------- | ---------- | ------------------------------------------------------------------------ |
| `name`      | `str`      | Constant identifier: `"run_item"`.                                       |
| `item`      | `RunItem`  | The completed run item (e.g. `MessageOutputItem`, `ToolCallItem`, etc.). |
| `timestamp` | `datetime` | When the event was emitted.                                              |

`item` itself exposes fields like:

- `item.type`: The specific subclass ("message_output", "tool_called", "tool_output", "handoff_requested", etc.)
- `item.content` or `item.result`: Payload data (text, tool inputs/outputs).
- `item.agent_name`: Which agent emitted this item.

## **AgentUpdatedStreamEvent:**

**Definition**

This dataclass represents the moment when the SDK switches active agents—typically following a handoff from one agent to another

**Purpose:**

- Signal Agent Transitions: In multi-agent workflows (e.g. a “triage” agent handing off to a “booking” agent), this event tells your application, “Hey, the next agent has taken over.”
- Drive UI/Logging Updates: Use it to update interface elements or logs so users/operators know which agent is now in control.

**Role on the Stage**

- Who Listens: Your event loop or UI controller in a run_streamed() consumer.

- When It Fires: Immediately after a handoff completes and the new agent begins processing.

- What It Enables: Dynamic adjustments—like changing the chat header to “Booking Agent” or routing subsequent inputs to the correct handler.

Inheritance
```nginx
StreamEvent  (TypeAlias)
├─ RawResponsesStreamEvent
├─ RunItemStreamEvent
└─ AgentUpdatedStreamEvent
```
AgentUpdatedStreamEvent is one of the three concrete variants of the StreamEvent union.

**Core Attributes**
| Attribute   | Type                                    | Description                                              |
| ----------- | --------------------------------------- | -------------------------------------------------------- |
| `new_agent` | `Agent[Any]`                            | The `Agent` instance that has just taken over execution. |
| `type`      | `Literal["agent_updated_stream_event"]` | A constant tag identifying this event kind.              |
---









<!-- ## **RunResultBase:**

**Role on the Stage**

Think of `RunResultBase` as the final report of everything your agent did once it stops running.

- Who reads it? Your application code, after the agent finishes.

- What it holds?

  - The final answer the agent produced (final_output).
  - A timeline of every step (new_items), from messages sent to tools used.
  - Any policy checks that passed or failed (guardrails).
  - The raw, low-level responses from the LLM provider (for debugging).

- When to use it? Whenever you need a complete record: logging, saving to a database, or chaining into the next turn.

**Inheritance**

```nginx
RunResultBase
├─ RunResult       (non-streamed)
└─ RunResultStreaming (streamed)
```

**Key behaviors**

- Aggregates all side-effects of a run into a single record.
- Provides helper methods like `to_input_list()` to reconstruct dialogue history. -->
