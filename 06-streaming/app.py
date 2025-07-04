import os
import asyncio
import random
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, ItemHelpers, AsyncOpenAI, set_tracing_disabled, OpenAIChatCompletionsModel, function_tool, RunResultStreaming

gemini_api_key = os.getenv("GEMINI_API_KEY")

client = AsyncOpenAI(api_key=gemini_api_key,
                     base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
set_tracing_disabled(True)


# ———— Streaming: Raw response events ————————————————————————————————

async def main():
    print("Running streaming example...")
    agent = Agent(
        name="Joker",
        instructions="You are a helpful assistant.",
        model=OpenAIChatCompletionsModel(
            model="gemini-2.0-flash", openai_client=client)
    )

    print("Agent created. Running...")
    result: RunResultStreaming = Runner.run_streamed(
        agent, input="Please tell me 5 jokes.")

    print("=== Run starting ===")
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

    print("\n=== Run complete ===")

if __name__ == "__main__":
    asyncio.run(main())


# ———— Streaming: Run item events and agent events  ————————————————————————————————

@function_tool
def how_many_jokes() -> int:
    return random.randint(1, 10)


async def main():
    print("Running streaming example with tool calls...")
    agent = Agent(
        name="Joker",
        instructions="First call the `how_many_jokes` tool, then tell that many jokes.",
        tools=[how_many_jokes],
        model=OpenAIChatCompletionsModel(
            model="gemini-2.0-flash", openai_client=client)
    )

    print("Agent created. Running...")
    result = Runner.run_streamed(agent, input="Hello")

    print("=== Run starting ===")

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

    print("=== Run complete ===")


if __name__ == "__main__":
    asyncio.run(main())
