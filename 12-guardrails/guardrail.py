import os
from pydantic import BaseModel
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, Agent, Runner, input_guardrail, RunContextWrapper, GuardrailFunctionOutput, TResponseInputItem, InputGuardrailTripwireTriggered


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"GEMINI_API_KEY: {GEMINI_API_KEY}")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)
print("OpenAI Client initialized with Gemini API key.")


class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

guardrail_agent = Agent(
    name="Guadrails Check",
    instructions="Check if the user is asking you to do their math homework.",
    model=model,
    output_type=MathHomeworkOutput,
)

print("Guardrail agent initialized.")


@input_guardrail
async def math_guardrail(ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_math_homework,
        # tripwire_triggered=False #result.final_output.is_math_homework,
    )

print("Guardrail function defined.")


agent = Agent(
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    model=model,
    input_guardrails=[math_guardrail],
)

print("Main agent initialized.")

try:
    result = Runner.run_sync(agent, "Hello, can you help me solve for x: 2x + 3 = 11?")
    print("Guardrail didn't trip - this is unexpected")
    print(result.final_output)

except InputGuardrailTripwireTriggered:
    print("Math homework guardrail tripped")
