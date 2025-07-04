# **Guardrails in the OpenAI Agent SDK**

Guardrails are validation hooks that run alongside your agent’s execution to enforce policies, sanitize inputs/outputs, and trigger alerts when certain conditions are met.

## **1. What Are Guardrails?**

Guardrails are functions or rules you attach to an Agent to check messages or tool results before they reach the LLM (input guardrails) or after the LLM produces its output (output guardrails). They help ensure safety, compliance, and data quality.

————————————— OR

Guardrails run in parallel to your agents, enabling you to do checks and validations of user input. For example, imagine you have an agent that uses a very smart (and hence slow/expensive) model to help with customer requests. You wouldn't want malicious users to ask the model to help them with their math homework. So, you can run a guardrail with a fast/cheap model. If the guardrail detects malicious usage, it can immediately raise an error, which stops the expensive model from running and saves you time/money.

There are two kinds of guardrails:

- Input guardrails run on the initial user input
- Output guardrails run on the final agent output

## **2. Why Do We Need Guardrails?**

- Safety & Compliance: Prevent disallowed content (e.g. profanity, PII) from being processed or emitted.
- Data Quality: Enforce formats, value ranges, or required fields.
- Operational Alerts: Tripwires can notify you when unusual patterns occur (e.g. high usage, error rates).

## **3. Where We Use Guardrails?**

- Chatbots: Block toxic language before it’s sent to the user.
- Financial Apps: Ensure numeric outputs are within expected bounds.
- Healthcare: Sanitize PHI before logging or downstream processing.
- Any Multi-step Workflow: Validate each tool’s output to prevent cascading errors.

## **4. How to Define Guardrails?**

Guardrails are defined as callable validators attached to an Agent via its input_guardrails and output_guardrails parameters.

```py
from agents import InputGuard, OutputGuard

agent = Agent(
    name="MyAgent",
    instructions="...",
    input_guardrails=[my_input_guard],
    output_guardrails=[my_output_guard]
)
```

## **5. Input Guardrails:**

### **What Are Input Guardrails?**

Input guardrails are validation hooks that run before any user message is fed into your agent’s LLM. Each guardrail inspects the raw input text (and optionally metadata) and returns a verdict—allow, block, or alert—so you can enforce safety, compliance, or data‑quality rules at the very first step.

### **How they work:**

Input guardrails run in 3 steps:

- First, the guardrail receives the same input passed to the agent.
- Next, the guardrail function runs to produce a GuardrailFunctionOutput, which is then wrapped in an InputGuardrailResult
- Finally, we check if .tripwire_triggered is true. If true, an InputGuardrailTripwireTriggered exception is raised, so you can appropriately respond to the user or handle the exception.

### **GuardrailFunctionOutput:**

`GuardrailFunctionOutput` is the standardized return type for any custom guardrail function in the Agent SDK. It’s a simple dataclass with two key fields:

1. `output_info: Any`

   - Optional payload carrying extra details about the guardrail’s evaluation.
   - For example, you might include which specific checks ran, counts of violations, or sanitized text.

2. `tripwire_triggered: bool`
   - Indicates whether the guardrail firing should be treated as a tripwire (an alert) or as a hard fail.
   - When tripwire_triggered=True, the SDK records the alert but continues execution.
   - When tripwire_triggered=False (the default for fail), the SDK treats it as a blocking failure.

### **InputGuardrailResult:**

An InputGuardrailResult is the object you get back when the Agent SDK runs an input guardrail against a user’s message. It bundles together:

1. `Which guardrail ran`

   - The .guardrail attribute holds the original InputGuardrail instance (i.e. the specific rule or function you defined).

2. `What the guardrail decided`
   - The .output attribute is a GuardrailFunctionOutput that tells you whether the input was allowed, blocked, or merely flagged (a tripwire).

### **.tripwire_triggered:**

- `What it is:` A boolean attribute on the GuardrailFunctionOutput dataclass that tells the SDK “this guardrail has fired a tripwire.”
- `What it means:` For input guardrails, any tripwire is treated as a blocking event: the agent run will be halted immediately, before calling the model or any tools. It’s a way to say “this input is so problematic (safety, compliance, cost, etc.) that we must stop right now.”

### **InputGuardrailTripwireTriggered**

- `What it is:` A custom exception subclass (AgentsException) that the SDK raises as soon as any input guardrail returns tripwire_triggered=True.

### **How to Implement Input Guardrails:**

With these building blocks—GuardrailFunctionOutput, InputGuardrailResult, .tripwire_triggered, and the exception—you can enforce any pre‑condition on user inputs, keeping your agent workflows safe and compliant.

```py
import os
from pydantic import BaseModel
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, Agent, Runner, input_guardrail, RunContextWrapper, GuardrailFunctionOutput, TResponseInputItem, InputGuardrailTripwireTriggered

class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

guardrail_agent = Agent(
    name="Guadrails Check",
    instructions="Check if the user is asking you to do their math homework.",
    model=model,
    output_type=MathHomeworkOutput,
)


@input_guardrail
async def math_guardrail(ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_math_homework,
        # tripwire_triggered=False #result.final_output.is_math_homework,
    )


agent = Agent(
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    model=model,
    input_guardrails=[math_guardrail],
)

try:
    result = Runner.run_sync(agent, "Hello, can you help me solve for x: 2x + 3 = 11?")
    print("Guardrail didn't trip - this is unexpected")
    print(result.final_output)

except InputGuardrailTripwireTriggered:
    print("Math homework guardrail tripped")
```

## **6. Output Guardrails:**

### **6.1 What Are Output Guardrails?**

Output guardrails are functions you attach to an Agent that inspect the agent’s LLM-generated response after it has been produced but before it’s returned to your code or user. They let you:

- Validate the format or content (e.g. enforce JSON schemas)
- Sanitize or redact sensitive information (e.g. PII)
- Block incorrect or disallowed outputs (trigger a hard stop)
- Alert on unusual or risky outputs (tripwires)

### **6.2 How they work:**

Output guardrails run in 3 steps:

- First, the guardrail receives the output produced by the agent.
- Next, the guardrail function runs to produce a GuardrailFunctionOutput, which is then wrapped in an OutputGuardrailResult
- Finally, we check if .tripwire_triggered is true. If true, an OutputGuardrailTripwireTriggered exception is raised, so you can appropriately respond to the user or handle the exception.

### **6.3 GuardrailFunctionOutput:**

Every guardrail—input or output—returns a GuardrailFunctionOutput, a simple dataclass with:

1. `output_info: Any`

   - Optional extra data about what the guardrail did or found (e.g. which fields failed validation).

2. `tripwire_triggered: bool`
   - When True, indicates a tripwire (alert) rather than a hard fail.
   - When tripwire_triggered=False, the SDK treats it as a blocking failure.

### **6.4 OutputGuardrailResult:**

An OutputGuardrailResult is the SDK’s way of packaging up everything you need to know after an output guardrail runs against an agent’s response. Think of it as a single record that tells you:

1. **Which guardrail ran**

   ```python
   result.guardrail  # the OutputGuardrail instance (the rule you attached)
   ```

2. **What the agent produced**

   ```python
   result.agent_output  # the raw value (text or structured object) the agent generated
   ```

3. **Which agent was checked**
   ```python
   result.agent  # the Agent instance whose output was validated
   ```
4. **What the guardrail decided**
   ```python
    result.output  # a GuardrailFunctionOutput with pass/fail/tripwire and any extra info
    ```

**Why It Matters**

- Auditability: You can log exactly which guardrail fired, on which agent, and against which content.

- Fine‑grained control: By inspecting result.output.tripwire_triggered, you know whether it was a hard failure (.fail()) or just an alert (.tripwire()).

- Error handling: If any guardrail returns a blocking failure, the SDK raises an OutputGuardrailTripwireTriggered exception carrying the very OutputGuardrailResult that failed, so you can catch it and surface a clear error message.

**Typical Workflow**

1. Agent generates agent_output.

2. For each guardrail in agent.output_guardrails, the SDK calls your checker function.

3. Each call returns a GuardrailFunctionOutput (pass/fail/tripwire).

4. The SDK wraps that in an OutputGuardrailResult, pairing it with agent_output, the guardrail itself, and the agent.

5. It then either:
   - Continues (if all guardrails passed or only tripwires fired), or
   - Raises OutputGuardrailTripwireTriggered(result) if any guardrail failed.

By using OutputGuardrailResult, you get a complete, structured snapshot of post‑generation policy checks—making it easy to log, debug, and enforce your system’s content rules.

### **6.5 .tripwire_triggered**
- **What it is:**
A boolean flag on the GuardrailFunctionOutput object returned by your guardrail function.

- **What it means**
    - True indicates that this particular guardrail has fired a tripwire—an alert that something is wrong.
    - For output guardrails, any tripwire (or fail) will halt the agent’s execution and raise an exception.

### **6.6 OutputGuardrailTripwireTriggered**
After your agent produces its output, the SDK runs each function you’ve wrapped with OutputGuardrail. If any of those guardrail functions returns a fail (i.e. GuardrailFunctionOutput.fail(...)), the SDK immediately raises OutputGuardrailTripwireTriggered instead of returning the response to your code.



## **7. Tripwires:**
Tripwires are special guardrails designed to alert you to notable conditions without necessarily blocking execution. They act as non‑fatal “warning bells” that trigger when predefined thresholds or patterns are met.

**Purpose**
- Monitor unusual or high‑risk situations (e.g., API cost spikes, repeated errors, unexpected content)
- Surface alerts in logs or dashboards while allowing the agent flow to continue

**Behavior**
- A guardrail function returns GuardrailFunctionOutput.tripwire(reason)
- The .tripwire_triggered flag in the result is set to True
- The SDK does not raise an exception for a tripwire; it simply records the event
- You can inspect or log all tripwire results after the run via run_result.input_guardrail_results or run_result.output_guardrail_results