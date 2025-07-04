import os
from typing import Any, List, Union
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, Agent, Runner, output_guardrail, RunContextWrapper, GuardrailFunctionOutput, TResponseInputItem, InputGuardrailTripwireTriggered


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"[Startup] GEMINI_API_KEY loaded: {bool(GEMINI_API_KEY)}")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)
print("[Startup] OpenAI Client initialized with Gemini API key.")


# Define the output guardrail to check for disallowed words
@output_guardrail
async def no_error_guardrail(ctx: RunContextWrapper, agent: Agent, output: Any) -> GuardrailFunctionOutput:
    output_str = str(output).lower()
    if "error" in output_str:
        return GuardrailFunctionOutput(output_info={"reason": "Output contains the word 'error'"}, tripwire_triggered=True)
    return GuardrailFunctionOutput(tripwire_triggered=False)

# Define the technical support agent
technical_support_agent = Agent(
    name="Technical Support",
    instructions="You are a technical support agent. Provide detailed technical solutions to user queries.",
    model=model,
    output_guardrails=[no_error_guardrail]
)

# Define the customer support agent with handoff to technical support
customer_support_agent = Agent(
    name="Customer Support",
    instructions="You are a customer support agent. Answer general customer queries politely. If the question is technical, hand off to the technical support agent.",
    model=model,
    handoffs=[technical_support_agent],
    output_guardrails=[no_error_guardrail]
)

async def main():
    result = await Runner.run(customer_support_agent, "I have a technical issue with my device.")
    print(result.final_output)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    print("[Done] Customer support agent executed with output guardrail.")