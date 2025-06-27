import os
import asyncio
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"GEMINI_API_KEY: {GEMINI_API_KEY}")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)


spanish_agent = Agent(
    name="Spanish Agent",
    instructions="You translate the user's message to Spanish.",
    model=model
)

french_agent = Agent(
    name="French  Agent",
    instructions="You translate the user's message to French.",
    model=model
)

turkish_agent = Agent(
    name="Turkish  Agent",
    instructions="You translate the user's message to Turkish.",
    model=model
)


async def main():
    orchestrator_agent = Agent(
        name="orchestrator_agent",
        instructions=(
            "You are a translation agent. You use the tools given to you to translate."
            "If asked for multiple translations, you call the relevant tools."
        ),
        model=model,
        tools=[
            spanish_agent.as_tool(
                tool_name="translate_to_spanish",
                tool_description="Translate the user's message to Spanish",
            ),
            french_agent.as_tool(
                tool_name="translate_to_french",
                tool_description="Translate the user's message to French",
            ),
            turkish_agent.as_tool(
                tool_name="translate_to_turkish",
                tool_description="Translate the user's message to Turkish",
            ),
        ],
    )

    result = await Runner.run(orchestrator_agent, "Translate 'Hello, how are you?' to Spanish, French & Turkish.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
    print("Done.")
