import os
import asyncio
from agents.exceptions import MaxTurnsExceeded, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from agents import Agent, Runner, RunConfig, ModelSettings, GuardrailFunctionOutput, input_guardrail, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled


# ─── 0. SET UP YOUR GEMINI CLIENT & TRACING ────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
set_tracing_disabled(disabled=True)


# ─── 1. INPUT GUARDRAIL ─────────────────────────────────────────────────
@input_guardrail
async def forbidden_content_guardrail(ctx, agent, input_data):
    """
    Tripwire if user input contains 'forbidden'.
    """
    text = ""
    if isinstance(input_data, str):
        text = input_data
    elif isinstance(input_data, list):
        # find last user message
        for item in reversed(input_data):
            if item.get("role") == "user":
                text = item.get("content", "")
                break
    if "forbidden" in text.lower():
        return GuardrailFunctionOutput(output_info=None, tripwire_triggered=True)
    return GuardrailFunctionOutput(output_info=None, tripwire_triggered=False)


# ─── 2. DEFINE YOUR AGENTS ────────────────────────────────────────────────
billing_agent = Agent(
    name="Billing Agent",
    instructions="You handle billing inquiries and process refunds.",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
)

technical_agent = Agent(
    name="Technical Agent",
    instructions="You handle technical support and troubleshooting questions.",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
)

triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "You are a support triage assistant. "
        "If the question is about billing or refunds, hand off to the Billing Agent. "
        "If it's about technical issues, hand off to the Technical Agent. "
        "Otherwise, answer directly."
    ),
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    handoffs=[billing_agent, technical_agent],
    input_guardrails=[forbidden_content_guardrail],
)

# ─── 5. MAIN ASYNC WORKFLOW ──────────────────────────────────────────────────────
async def main():

    # Part A: Normal run with input guardrail
    print("\n--- Part A: Standard Triage Run ---")
    try:
        result = await Runner.run(triage_agent, "I was double charged last month; how do I get a refund?")
        print("Final Output:", result.final_output)
        
    except InputGuardrailTripwireTriggered:
        print("🚨 Input guardrail triggered: forbidden content detected.")
    except MaxTurnsExceeded:
        print("Error: Exceeded maximum turns in Part A.")
    except OutputGuardrailTripwireTriggered:
        print("Error: Output guardrail triggered in Part A.")


    # Part B: Forced tool_choice via RunConfig
    print("\n--- Part B: Forced tool_choice via RunConfig ---")
    forced_cfg = RunConfig(
        model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
        model_settings=ModelSettings(tool_choice="required")
    )

    try:
        result2 = await Runner.run(triage_agent, "My app crashes when I open it. What should I do?", run_config=forced_cfg)
        print("Final Output with forced tool_choice:", result2.final_output)
    except InputGuardrailTripwireTriggered:
        print("🚨 Input guardrail triggered in Part B.")
    except MaxTurnsExceeded:
        print("Error: Exceeded maximum turns in Part B.")
    except OutputGuardrailTripwireTriggered:
        print("Error: Output guardrail triggered in Part B.")

if __name__ == "__main__":
    asyncio.run(main())