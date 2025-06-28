import os
import random
import asyncio
from agents.exceptions import MaxTurnsExceeded
from agents import Agent, Runner, function_tool, RunConfig, ModelSettings, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled


# ─── 0. SET UP YOUR GEMINI CLIENT & TRACING ────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
set_tracing_disabled(disabled=True)


# ─── 1. DEFINE YOUR TOOL ─────────────────────────────────────────────────────────────
@function_tool
def how_many_jokes() -> int:
    """Return a random number of jokes to tell."""
    return random.randint(1, 5)


# ─── 2. DEFINE YOUR AGENT ─────────────────────────────────────────────────────────────
joke_agent = Agent(
    name="Joke Agent",
    instructions=(
        "First call the `how_many_jokes` tool to get a number N, "
        "then tell N one-line jokes."
    ),
    model=OpenAIChatCompletionsModel(
        model="gemini-1.5-flash", openai_client=client),
    tools=[how_many_jokes],
)


# ─── 3. MAIN ASYNC WORKFLOW ───────────────────────────────────────────────────────────
async def main():

    # A) Force tool use via RunConfig
    custom_cfg = RunConfig(
        model=OpenAIChatCompletionsModel(model="gemini-1.5-flash", openai_client=client),
        model_settings=ModelSettings(tool_choice="required")
    )

    # B) Trigger MaxTurnsExceeded by setting max_turns=2
    print("\n--- Run with max_turns=2 to trigger exception ---")
    try:
        # With max_turns=2, the agent won't have enough turns to call the tool and finish
        print("\n--- Run with forced tool_choice ---")
        result = await Runner.run(joke_agent, "Tell me a joke.", run_config=custom_cfg, max_turns=2)

        print("\n --- Joke Agent says: ---")
        print(result.final_output)

    except MaxTurnsExceeded:
        print("✅ Handled exception: MaxTurnsExceeded (max_turns=2)")

if __name__ == "__main__":
    asyncio.run(main())



# ─── Some Theory Regarding to this code ───────────────────────────────────────────────────────────\
# When you set max_turns=1, you’re telling the Agent SDK “allow only one iteration of the agent loop before giving up.” A “turn” in this context is one cycle of:
    # 1. LLM → Agent call (the model sees instructions + inputs and replies),
    # 2. Optional Tool Invocation (if the model asked to call a tool, that counts as the same turn),
    # 3. Appending the result back into the conversation.


# In your joke-agent example, the agent needs at least two turns:
    # Turn 1: The agent calls the how_many_jokes tool (it asks “how many jokes?” and runs that function).
    # Turn 2: The agent takes the tool’s numeric result and generates its final output (the actual jokes).
# If you only allow one turn, the loop ends immediately after it calls the tool (or after the first LLM reply), so it never gets to the “tell the jokes” step—and the SDK raises MaxTurnsExceeded to prevent an infinite or incomplete run.


# When you raise max_turns to 5, you give the agent enough turns (up to five) to:
# 1. Call the tool,
# 2. Process its output,
# 3. Generate and return the final text.

# That’s why you see the error at max_turns=1, but it works when you allow more turns.







