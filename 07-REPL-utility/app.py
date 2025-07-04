import os
import asyncio
from agents import Agent, Runner, AsyncOpenAI, set_tracing_disabled, OpenAIChatCompletionsModel, run_demo_loop

gemini_api_key = os.getenv("GEMINI_API_KEY")
print("GEMINI_API_KEY:", gemini_api_key)

client = AsyncOpenAI(api_key=gemini_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
set_tracing_disabled(True)


# ———— Streaming: Raw response events ————————————————————————————————
async def main():
    print("Running streaming example...")
    agent = Agent(
        name="Joker",
        instructions="You are a helpful assistant.",
        model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
    )

    await run_demo_loop(agent)

if __name__ == "__main__":
    asyncio.run(main())
