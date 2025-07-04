import os
import asyncio
from pydantic import BaseModel
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, Agent, Runner, input_guardrail, RunContextWrapper, GuardrailFunctionOutput, TResponseInputItem, InputGuardrailTripwireTriggered


# —————————————
# 1. Load API key & initialize model
# —————————————
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"[Startup] GEMINI_API_KEY loaded: {bool(GEMINI_API_KEY)}")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)
print("[Startup] OpenAI Client initialized with Gemini API key.")


# —————————————
# 2. A “basic” guardrail function
# —————————————
def basic_guardrail(user_input: str) -> bool:
    """
    Naïve check: if input contains both "solve" and "=",
    we consider it a direct homework request and block it.
    """
    text = user_input.lower()
    return not ("solve" in text and "=" in text)


# —————————————
# 3. Wrap that basic check in an @input_guardrail
# —————————————
@input_guardrail
async def naive_math_guardrail(ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
    # Extract raw text if a list of TResponseInputItem was passed
    user_text = input if isinstance(input, str) else input[0].text

    allowed = basic_guardrail(user_text)
    print(f"[Guardrail] basic check on `{user_text}` → allowed={allowed}")

    return GuardrailFunctionOutput(
        output_info={"allowed": allowed},
        tripwire_triggered=not allowed  # block when allowed==False
    )



# —————————————
# 4. Your main “Customer Support” agent
# —————————————
support_agent = Agent(
    name="Customer Support Agent",
    instructions="You are a helpful customer support agent.",
    model=model,
    input_guardrails=[naive_math_guardrail]
)

print("[Setup] Main agent initialized with naive_math_guardrail.")


# —————————————
# 5. Test it with a few prompts
# —————————————
async def test():
    prompts = [
        "Please solve x + 2 = 5 for me.",           # should trip
        "Can you explain how equations work?",      # should pass
        "What's 7 + 3?",                            # should trip (naive)
        "How do I change my account password?"      # should pass
    ]

    for p in prompts:
        print(f"\n[User] {p}")
        try:
            resp = await Runner.run(support_agent, p)
            print("[Agent] ✅ Response:", resp.final_output)
        except InputGuardrailTripwireTriggered:
            print("[Agent] ⛔ Guardrail tripped — refusing to do homework")

if __name__ == "__main__":
    asyncio.run(test())
