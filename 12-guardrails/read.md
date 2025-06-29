# **Guardrails in OpenAI Agent SDK**

Guardrails in the OpenAI Agent SDK are essential tools designed to ensure the safety, compliance, and quality of interactions between users and AI agents. This detailed guide, based on the provided resource, simplifies the technical documentation to make it accessible for a broader audience, without adding new information. It covers the purpose, types, implementation, and use cases of guardrails, with a focus on input and output guardrails, as well as tripwires.

## **Introduction to Guardrails**

Guardrails are validation hooks that run alongside an agent's execution. They enforce policies, sanitize inputs and outputs, and trigger alerts when certain conditions are met. There are two main categories: input guardrails and output guardrails, each serving distinct purposes in maintaining the integrity of agent interactions.

- **Input Guardrails:** These check user messages before they reach the agent's language model (LLM). They ensure safety and compliance by inspecting raw input text and optionally metadata, returning a verdict to allow, block, or alert.
- **Output Guardrails:** These validate the agent's LLM-generated response after production but before it is returned. They can enforce formats, sanitize sensitive information, block incorrect outputs, or alert on risky content.

The need for guardrails arises from the necessity to maintain safety, ensure data quality, and provide operational alerts. They prevent disallowed content, enforce data formats, and notify when unusual patterns, such as high usage or error rates, occur.

## **Key Points**

- Guardrails in the OpenAI Agent SDK are safety checks to ensure inputs and outputs are safe and follow rules.
- They include input guardrails (checking user messages) and output guardrails (checking agent responses).
- Research suggests they help with safety, data quality, and alerting on unusual activity.
- The evidence leans toward their use in chatbots, finance, healthcare, and workflows.


## Where Are They Used?

Research suggests guardrails are used in:

- Chatbots to block harmful language.
- Financial apps to check numbers are correct.
- Healthcare to protect sensitive info.
- Any process with multiple steps to avoid mistakes.



## **Use Cases of Guardrails**

Guardrails find applications across various domains, enhancing the reliability and safety of AI interactions:

- **Chatbots:** Block toxic or harmful language before it reaches the user.
- **Financial Apps:** Ensure numeric outputs are within expected bounds to prevent errors.
- **Healthcare:** Sanitize protected health information (PHI) before logging or processing downstream.
- **Multi-step Workflows:** Validate each tool's output to prevent cascading errors in complex processes.

## **Defining and Implementing Guardrails**

Guardrails are defined as callable validators attached to an agent via its `input_guardrails` and `output_guardrails` parameters. For example, you can set them up as follows:

```python
from agents import InputGuard, OutputGuard

agent = Agent(
    name="MyAgent",
    instructions="...",
    input_guardrails=[my_input_guard],
    output_guardrails=[my_output_guard]
)
```

This setup allows you to integrate custom validation functions into the agent's workflow, ensuring checks are performed at critical points.

## **Detailed Look at Input Guardrails**

Input guardrails are crucial for pre-processing user inputs. They run in three steps:

1. The guardrail receives the same input passed to the agent.
2. The guardrail function runs, producing a `GuardrailFunctionOutput`, which is wrapped in an `InputGuardrailResult`.
3. The system checks if `.tripwire_triggered` is true; if so, an `InputGuardrailTripwireTriggered` exception is raised, halting the process.

### **Key Components:**

- **GuardrailFunctionOutput:** A standardized return type with two fields:
  - `output_info`: Optional payload carrying extra details, like which checks ran or violation counts.
  - `tripwire_triggered`: A boolean indicating if the guardrail fired a tripwire (alert) or caused a hard fail. When `tripwire_triggered=True`, the SDK records the alert but continues; when `False`, it blocks execution.
- **InputGuardrailResult:** Bundles which guardrail ran, what it decided, and the output, providing auditability and control.
- **.tripwire_triggered:** For input guardrails, any tripwire is treated as a blocking event, stopping the agent run before calling the model or tools.
- **InputGuardrailTripwireTriggered:** A custom exception raised when `tripwire_triggered=True`, allowing appropriate user responses or exception handling.

### **Implementation Example:**

Consider a scenario where you want to prevent users from asking the agent to do math homework, which could be costly or inappropriate. You can implement an input guardrail as follows:

```python
import os
from pydantic import BaseModel
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, Agent, Runner, input_guardrail, RunContextWrapper, GuardrailFunctionOutput, TResponseInputItem, InputGuardrailTripwireTriggered

class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

guardrail_agent = Agent(
    name="Guardrails Check",
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

This example shows how to create and attach an input guardrail to check for math homework requests, stopping the process if detected.

## **Detailed Look at Output Guardrails**

Output guardrails inspect the agent's response after generation but before return. They run in three steps:

1. The guardrail receives the output produced by the agent.
2. The guardrail function runs, producing a `GuardrailFunctionOutput`, wrapped in an `OutputGuardrailResult`.
3. The system checks if `.tripwire_triggered` is true; if so, an `OutputGuardrailTripwireTriggered` exception is raised.

### **Key Components:**

- **GuardrailFunctionOutput:** Similar to input guardrails, with `output_info` for extra details and `tripwire_triggered` for alerts or fails.
- **OutputGuardrailResult:** Packages which guardrail ran, what the agent produced, which agent was checked, and what the guardrail decided, providing auditability and fine-grained control.
- **.tripwire_triggered:** Indicates if the guardrail fired a tripwire. For output guardrails, any tripwire or fail halts execution, raising an exception.
- **OutputGuardrailTripwireTriggered:** Raised when any output guardrail returns a fail, stopping the response from being sent.

### **Typical Workflow:**

1. The agent generates its output.
2. Each output guardrail runs, returning a `GuardrailFunctionOutput`.
3. The SDK wraps results in `OutputGuardrailResult`, continuing if all pass or only tripwires fire, or raising `OutputGuardrailTripwireTriggered` if any fail.

## **Tripwires: Non-Fatal Alerts**

Tripwires are special guardrails designed to alert on notable conditions without blocking execution. They act as non-fatal "warning bells" for monitoring:

- Purpose: Monitor unusual or high-risk situations, like API cost spikes or repeated errors, and surface alerts in logs or dashboards.
- Behavior: A guardrail function returns `GuardrailFunctionOutput.tripwire(reason)`, setting `.tripwire_triggered=True`. The SDK records the event but does not raise an exception, allowing the agent flow to continue. You can inspect tripwire results via `run_result.input_guardrail_results` or `run_result.output_guardrail_results`.

## **Comparative Analysis: Input vs. Output Guardrails**

To better understand the differences, here’s a table summarizing key aspects:

| **Aspect**           | **Input Guardrails**                     | **Output Guardrails**                            |
| -------------------- | ---------------------------------------- | ------------------------------------------------ |
| **When They Run**    | Before user input reaches the LLM        | After LLM generates response, before return      |
| **Purpose**          | Validate and sanitize user input         | Validate, sanitize, or block agent output        |
| **Key Check**        | Inspect raw input text and metadata      | Inspect agent-generated response                 |
| **Outcome**          | Allow, block, or alert (tripwire blocks) | Allow, block, or alert (tripwire or fail blocks) |
| **Exception Raised** | `InputGuardrailTripwireTriggered`        | `OutputGuardrailTripwireTriggered`               |
| **Example Use Case** | Block math homework requests             | Ensure response format is JSON                   |

This table highlights the distinct roles and behaviors of input and output guardrails, aiding in their implementation and understanding.

#### Conclusion

Guardrails in the OpenAI Agent SDK are vital for ensuring safe and compliant AI interactions. Input guardrails protect against problematic user inputs, while output guardrails safeguard the agent's responses. Tripwires provide additional monitoring without halting execution, enhancing operational awareness. This guide, based on the provided resource, simplifies the technical details for easier comprehension, covering all aspects from definition to implementation, without adding extraneous information.

