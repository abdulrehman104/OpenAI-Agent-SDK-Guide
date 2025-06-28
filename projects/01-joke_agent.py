import os
import random
import asyncio
from agents import Agent, Runner, function_tool, ItemHelpers, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled


# ─── SET UP YOUR GEMINI CLIENT & TRACING ─────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
set_tracing_disabled(disabled=True)


# ─── 1. DEFINE YOUR TOOL ─────────────────────────────────────────────────────────────

@function_tool
def how_many_jokes() -> int:
    """Return a random number of jokes to tell."""
    return random.randint(1, 3)


# ─── 2. DEFINE YOUR AGENT (USING gemini-1.5-flash) ─────────────────────────────────

joke_agent = Agent(
    name="Joke Agent",
    instructions=(
        "First call the `how_many_jokes` tool to determine how many jokes to tell, "
        "then tell that many jokes."
    ),
    model=OpenAIChatCompletionsModel(
        model="gemini-1.5-flash",
        openai_client=client
    ),
    tools=[how_many_jokes],
)


# ─── 3. STREAMING WORKFLOW ──────────────────────────────────────────────────────────

async def main():
    print("\n─── Streaming Joke Agent ───")

    # Start the streaming run
    result = Runner.run_streamed(joke_agent, input="Hello")

    print("\n─── Run starting ───")

    # Iterate over streaming events
    async for event in result.stream_events():
        # We'll ignore the raw responses event deltas
        if event.type == "raw_response_event":
            continue
        # When the agent updates, print that
        elif event.type == "agent_updated_stream_event":
            print(f"Agent updated: {event.new_agent.name}")
            continue
        # When items are generated, print them
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print("-- Tool was called")
            elif event.item.type == "tool_call_output_item":
                print(f"-- Tool output: {event.item.output}")
            elif event.item.type == "message_output_item":
                print(
                    f"-- Message output:\n {ItemHelpers.text_message_output(event.item)}")
            else:
                pass  # Ignore other event types


# ─── 4. RUNNING Agent ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main())
