# **Handoffs in the OpenAI Agent SDK**

Handoffs enable one agent to delegate part of its task to another agent during a run. They are essential for splitting responsibilities and maintaining clear, modular workflows in multi-agent systems.

## **1. What Are Handoffs?**

A handoff is a mechanism where an active agent stops its own processing and transfers control (and context) to a specified sub-agent. The sub-agent then runs its own instructions and tools, producing an output that feeds back into the original agent’s flow.

**Key benefits:**

- Clear separation of concerns
- Reusable specialist agents
- Simplified orchestration of complex workflows

## **2. Creating a Handoff:**

You declare handoffs when constructing an Agent. Provide a list of other Agent instances via the handoffs parameter:

```py
from agents import Agent

# Define sub-agents
flight_agent = Agent(name="FlightAgent", instructions="Search flights...")
hotel_agent  = Agent(name="HotelAgent",  instructions="Search hotels...")

# Coordinator agent with handoffs
planner = Agent(
    name="TravelPlanner",
    instructions="Delegate searches to sub-agents.",
    handoffs=[flight_agent, hotel_agent]
)
```

Now planner can call either sub-agent by name.

## **3. Basic Usage:**

Within the parent agent’s instructions, reference sub-agents by their name. When the LLM emits a JSON call specifying tool equal to a sub-agent’s name, the SDK triggers the handoff automatically:

```py
planner = Agent(
    name="TravelPlanner",
    instructions=(
        "To find flights, call FlightAgent. "
        "To find hotels, call HotelAgent."
    ),
    handoffs=[flight_agent, hotel_agent]
)

result = Runner.run_sync(planner, "I need a flight and a hotel in Paris.")
```

The SDK routes the request to FlightAgent or HotelAgent as the LLM decides.

## **4. Customizing Handoffs via handoff():**

For more control over handoffs, you can use the handoff() function instead of passing agents directly to the handoffs parameter:

The handoff() function lets you customize things.

- `agent:` This is the agent to which things will be handed off.
- `tool_name_override:` By default, the `Handoff.default*tool_name()` function is used, which resolves to `transfer_to*<agent_name>`. You can override this.
- `tool_description_override:` Override the default tool description from `Handoff.default_tool_description()`
- `on_handoff:` A callback function executed when the handoff is invoked. This is useful for things like kicking off some data fetching as soon as you know a handoff is being invoked. This function receives the agent context, and can optionally also receive LLM generated input. The input data is controlled by the `input_type` param.
- `input_type:` The type of input expected by the handoff (optional).
- `input_filter:` This lets you filter the input received by the next agent. See below for more.

  ```py
  from agents import Agent, handoff, RunContextWrapper

  def on_handoff(ctx: RunContextWrapper[None]):
      print("Handoff called")

  agent = Agent(name="My agent")

  handoff_obj = handoff(
      agent=agent,
      on_handoff=on_handoff,
      tool_name_override="custom_handoff_tool",
      tool_description_override="Custom description",
  )
  ```

## **5. Handoff inputs:**

### **Defination:**

Sometimes, you want the first agent to provide additional context or metadata when handing off to another agent. The Agents SDK supports this through the input_type parameter:

—————————— OR

In certain situations, you want the LLM to provide some data when it calls a handoff. For example, imagine a handoff to an "Escalation agent". You might want a reason to be provided, so you can log it.

—————————— OR

Handoff inputs let you require the LLM to supply structured data when it invokes a handoff tool. Instead of simply transferring the conversation, the agent can ask the LLM to fill in fields you’ve defined (e.g., a “reason” for escalation) and pass them along to the receiving agent.

### **How they work:**

1. You declare a Pydantic model (BaseModel subclass) that describes exactly what data the LLM must provide.
2. You pass that model as the input_type argument to the handoff() function.
3. When the handoff tool is called, the SDK runs the LLM, parses its JSON output into your model, and passes the resulting object into your callback (on_handoff).

### **Key parameters in handoff():**

```py
from pydantic import BaseModel

from agents import Agent, handoff, RunContextWrapper

class EscalationData(BaseModel):
    reason: str

async def on_handoff(ctx: RunContextWrapper[None], input_data: EscalationData):
    print(f"Escalation agent called with reason: {input_data.reason}")

agent = Agent(name="Escalation agent")

handoff_obj = handoff(
    agent=agent,
    on_handoff=on_handoff,
    input_type=EscalationData,
)
```

## **6. Input Filters:**

### **What is an input filter?**

An **input filter** is a pure‑Python function you can pass to your `handoff()` call that takes the usual full handoff input (a `HandoffInputData` object) and returns a _new_ `HandoffInputData`. In effect, it lets you **modify exactly what pieces of the prior conversation** are passed along to the next agent, instead of handing over the full history verbatim ([openai.github.io][1]).

### **Why use an input filter?**

By default, when you hand off to another agent, that agent “sees” the _entire_ preceding chat history. Sometimes you need to:

- **Remove irrelevant tool calls** (so a FAQ bot doesn’t get confused by billing‑agent prompts)
- **Filter out sensitive data** (e.g. PII or internal debugging details)
- **Trim the history** to just the last N turns, or to only user messages
- **Translate or normalize** pieces of the context before passing it on

An input filter gives you complete control over that transformation ([openai.github.io][1]).

### **When to use an input filter:**

Use an input filter whenever you want the _receiving_ agent to get a tailored context rather than everything that’s happened so far. Typical scenarios include:

- **Specialized agents** (e.g. FAQ, billing, escalation) shouldn’t see irrelevant tool‑invocation chatter
- **Security**: strip out tokens or internal URLs before passing data
- **Performance**: shorten very long conversations to a manageable size
- **Data shaping**: extract only certain fields from a structured handoff payload

If you don’t need any of this, you can omit `input_filter` and let the full history through.

### **How to wire up an input filter:**

```py

```

### **Built‑in filters:**

The SDK ships with a handful of common filters under `agents.extensions.handoff_filters`, for example:

- `remove_all_tools`: remove _every_ tool invocation from the history
- (you can explore others or write your own in the same shape)

## **7. Recommended Prompts:**
