# **Agent:**

An **Agent** in the OpenAI Agent SDK is your programmable AI worker—a combination of a language model, a set of instructions, and optional tools or sub-agents. Agents can carry on conversations, make API calls, perform calculations, and orchestrate multi-step workflows. Below is a detailed breakdown of all key aspects.

## **1. Definition:**

An Agent is:

- **A model instance** (e.g. GPT-4, Claude, Gemini) wrapped in SDK code.
- **A system prompt** (called **instructions**) that tells the model how to behave — its role, style, and boundaries.
- **A tool registry**: a list of Python functions or other agents it can invoke.

Together, these pieces let the Agent understand user input, decide when and how to call tools, and produce useful results.

## **2. Basic configuration:**

When you create an Agent, you specify:

1. **Name**: A short label (e.g. `"HaikuBot"`) to identify it in logs and traces.
2. **Instructions**: A clear directive (e.g. `"Always respond in haikus"`).
3. **Model**: Which LLM to use, model name (e.g. `"gpt-4"`)
4. **Tools** (optional): Functions decorated with `@function_tool` that the agent can call.

    ```python
    from agents import Agent, function_tool

    @function_tool
    def get_time() -> str:
        return datetime.now().isoformat()

    # Create an agent that can tell the current time
    time_agent = Agent(
        name="TimeKeeper",
        instructions="You answer time queries.",
        model="gpt-4",
        tools=[get_time],
    )
    ```

## **3. Context:**

**Context** is a structured data object you define and pass into every agent run. It lets you carry important information through the entire workflow, without relying on global variables. Common uses include:

- **User data**: IDs, preferences, or access tokens (e.g. `user_id`, `is_premium`).
- **Shared resources**: Database connections, HTTP clients, or feature flags.
- **Immutable settings**: Configuration options or environment-specific flags.

By injecting context, your tool functions remain pure, stateless, and easy to test. The SDK ensures the same context instance travels with every step, from LLM calls to tool invocations and sub-agent handoffs.

```python
from dataclasses import dataclass
from agents import Agent

@dataclass
class RequestContext:
    user_id: str
    is_admin: bool

# The lambda reads from ctx to choose the right greeting
greet_agent = Agent[RequestContext](
    name="Greeter",
    instructions=lambda ctx: (
        "Hello, admin!" if ctx.is_admin else "Hello, guest!"
    ),
    model="gpt-4",
)
```

The `AppContext` travels unmodified through each step, ensuring your tools always have the resources they need.

## **4. Output types:**

By default, Agents return plain **text** (`str`). To get structured data, set an **output_type** using a Pydantic model:

```python
from pydantic import BaseModel

class WeatherReport(BaseModel):
    city: str
    temperature: float
    condition: str

weather_agent = Agent(
    name="WeatherParser",
    instructions="Extract weather details in JSON.",
    model="gpt-4",
    output_type=WeatherReport,
)
```

The SDK will parse the model’s text into your `WeatherReport` fields, raising errors if something is missing or malformed.

## **5. Handoffs:**

**Handoffs** allow one Agent to delegate a task to another, more specialized Agent:

1. **Parent Agent** defines `handoffs=[child_agent]`.
2. On detecting a relevant need, it emits a **handoff request** event.
3. The SDK automatically runs `child_agent` with the same context and input.

Use handoffs when you have clear sub-domains (e.g. booking flights vs. booking hotels). This keeps each agent’s logic simple.

```python
from agents import Agent

booking_agent = Agent(...)
refund_agent = Agent(...)

triage_agent = Agent(
    name="Triage agent",
    instructions=(
        "Help the user with their questions."
        "If they ask about booking, handoff to the booking agent."
        "If they ask about refunds, handoff to the refund agent."
    ),
    handoffs=[booking_agent, refund_agent],
)
```

## **6. Dynamic instructions:**

Instead of static text, **instructions** can be a function that returns different prompts based on context or agent state. This enables per-user or per-session behavior changes without rewriting agent definitions.

```python
from dataclasses import dataclass
from agents import Agent

@dataclass
class UserContext:
    user_id: str
    is_vip: bool

# Function to generate instructions dynamically
def make_instructions(ctx: UserContext, agent: Agent) -> str:
    if ctx.is_vip:
        return (
            f"Hello VIP {ctx.user_id}! You have exclusive access to premium features."
        )
    else:
        return (
            f"Hello {ctx.user_id}. You are currently on the free tier."
        )

vip_agent = Agent[UserContext](
    name="WelcomeAgent",
    instructions=make_instructions,
    model="gpt-4",
)

# When you run:
# ctx = UserContext(user_id="alice123", is_vip=True)
# The system prompt will read: "Hello VIP alice123! You have exclusive access to premium features.
```

**Advanced Scenario: Contextual Task Switching:**

Imagine an agent that can either help with support tickets or provide sales info based on the user’s request:

```python
from dataclasses import dataclass
from agents import Agent

@dataclass
class SessionContext:
    user_id: str
    intent: str  # e.g. 'support' or 'sales'

# Dynamic instructions choose a task-specific prompt
def task_instructions(ctx: SessionContext, agent: Agent) -> str:
    if ctx.intent == 'support':
        return "You are a helpful support assistant. Resolve user issues step by step."
    elif ctx.intent == 'sales':
        return "You are a persuasive sales assistant. Recommend products based on user needs."
    else:
        return "You are a general assistant. How can I help?"

multi_task_agent = Agent[SessionContext](
    name="TaskAgent",
    instructions=task_instructions,
    model="gpt-4",
)
```

In this setup, **dynamic instructions** let the same agent adapt its behavior instantly based on the `intent` field in context.

## **7. Lifecycle events (hooks):**

**AgentHooks** let you run custom code at key moments during an agent’s execution:

- **on_start**: Before the agent begins. Great for logging the input or setting up timers.
- **on_end**: After the agent finishes. Use it to log the final output or clean up resources.
- **on_handoff**: When one agent passes control to another. Helpful for tracking which agent is handling a sub-task.
- **on_tool_start**: Right before a tool runs. Perfect for validating inputs or starting a stopwatch.
- **on_tool_end**: Right after a tool completes. Good for inspecting results, caching, or stopping the timer.

**How to use:**

1. Subclass `AgentHooks` and override the methods you need.
2. Attach your hook class to an agent via `hooks=YourHooks()`.

That’s it—hooks give you simple, granular control and visibility into every step of your agent’s work.

## **8. Guardrails:**

Guardrails are built-in safety nets that run _alongside_ your agent to ensure inputs and outputs remain valid, safe, and compliant. They work by intercepting messages at two stages:

1. **Input Guards**: Trigger **before** the LLM sees the user prompt.
   - Validate or sanitize user messages.
   - Enforce format rules (e.g., email must match a regex).
   - Block requests that violate policies (e.g., disallowed content).
2. **Output Guards**: Trigger **after** the LLM generates a response but **before** it’s returned to the caller.
   - Clean or redact sensitive data (PII, profanity).
   - Ensure structured outputs match schemas.
   - Reject or transform any unexpected content.

## How Guardrails Work

- You define guard rules using Pydantic models, custom functions, or policy definitions.
- The SDK automatically applies them in sequence: input → agent run → output.
- Guard failures can raise exceptions, return fallback messages, or trigger alternative workflows.

## **9. Cloning/copying agents:**

**What It Means:**

Cloning (or copying) an agent makes a new agent that starts with exactly the same setup—same model, instructions, tools, and hooks—as an existing one. After cloning, you can tweak only the bits you need (like its name or instructions) without rewriting all the configuration.

**Why It’s Helpful:**

1. **Reusability**
   - Define a “base” agent once.
   - Create specialized versions (e.g. “PirateBot”, “FormalBot”) from that base, rather than repeating the setup.
2. **Consistency**
   - All clones share the same tested core settings, so you avoid typos or mismatches.
3. **Simplicity**
   - Keeps your code DRY (Don’t Repeat Yourself).
   - Easy to manage many similar agents without copy-pasting large blocks of code.

**How to Clone:**

```python
from agents import Agent

# 1. Define a base agent
base_agent = Agent(
    name="BaseBot",
    instructions="You are a helpful assistant.",
    model="gpt-4",
    # tools, hooks, output_type, etc., if needed
)

# 2. Clone into a pirate-themed agent
pirate_agent = base_agent.clone(
    name="PirateBot",
    instructions="You speak like a pirate: use 'Ahoy' and 'Matey'."
)

# 3. Clone into a formal-tone agent
formal_agent = base_agent.clone(
    name="FormalBot",
    instructions="You speak in a very formal and polite tone."
)
```

- **`base_agent.clone(...)`** returns a brand-new `Agent` object.
- You can override any subset of parameters (name, instructions, model settings, tools, etc.) in the `clone()` call.

## **10. Forcing tool use:**

The `tool_choice` setting in `ModelSettings` lets you control whether and how the agent uses tools for each run:

- **`auto`** (default): The LLM decides if and when to call any tool.
- **`required`**: The agent must call _at least one_ tool before producing its final response.
- **`"tool_name"`**: The agent must call the specified tool (`tool_name`) first, then complete its response.
- **`none`**: The agent is prohibited from calling any tools during this run.

You can set this globally on the Agent or override it per run using `runner.run_sync(..., run_config=RunConfig(tool_choice=...))`. To reset a forced tool choice back to `auto` within a session, use `agent.reset_tool_choice()`.

These options give you precise control over tool invocation, ensuring your agent behaves exactly as needed for each scenario.
