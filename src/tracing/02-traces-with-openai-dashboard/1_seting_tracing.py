import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, trace


# ———— Load Env & Setup LLM ————————————————————————————————
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-1.5-flash", openai_client=client)


# ———— Main Function to Executing Agent ————————————————————————————————
async def main():
    print(f"Processing inquiry:")

   # Create a triage agent that can hand off to specialists
    agent = Agent(name="Joke generator", instructions="Tell funny jokes.", model=model)
    
    with trace("Joke workflow"): 
        first_result = await Runner.run(agent, "Tell me a joke")
        second_result = await Runner.run(agent, f"Rate this joke: {first_result.final_output}")
        print(f"Joke: {first_result.final_output}")
        print(f"Rating: {second_result.final_output}")

if __name__ == "__main__":

    asyncio.run(main())