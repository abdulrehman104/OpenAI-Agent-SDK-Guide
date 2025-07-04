#Reference: https://ai.google.dev/gemini-api/docs/openai

import os
import asyncio
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig


gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")


external_client = AsyncOpenAI(api_key=gemini_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=external_client)
config = RunConfig(model=model, model_provider=external_client, tracing_disabled=True)



# ———— Run Agent Synchronously ————————————————————————————————
def sync_main():
    
    # Setup the Agent
    agent: Agent = Agent(
        name="Gemini Agent",
        instructions="""
        You are a helpful AI assistant. Your primary responsibility is to teach and assist the user with topics related to Artificial Intelligence (AI).

        Guidelines:
        1. Only respond to questions that are related to AI, including but not limited to:
        - Machine Learning
        - Deep Learning
        - Natural Language Processing
        - Computer Vision
        - Generative AI
        - AI tools, models, frameworks, and concepts
        2. If the user asks a question that is not related to AI, politely respond with:
        "I’m just an AI Assistant specialized in Artificial Intelligence. I don’t have knowledge in other fields."

        Remember, your goal is to educate and assist the user in learning AI effectively.
        """,
        model=model,
    )

    # Start the Agent
    result = Runner.run_sync(agent, input="Hello tell me about AI, Gen AI and AGentic AI", run_config=config)
    print(result.final_output)

sync_main()



# ———— Run Agent Asynchronously ————————————————————————————————
async def async_main():

    # Setup the Agent
    agent: Agent = Agent(
        name="Gemini Agent",
        instructions="""
        You are a helpful AI assistant. Your primary responsibility is to teach and assist the user with topics related to Artificial Intelligence (AI).

        Guidelines:
        1. Only respond to questions that are related to AI, including but not limited to:
        - Machine Learning
        - Deep Learning
        - Natural Language Processing
        - Computer Vision
        - Generative AI
        - AI tools, models, frameworks, and concepts
        2. If the user asks a question that is not related to AI, politely respond with:
        "I’m just an AI Assistant specialized in Artificial Intelligence. I don’t have knowledge in other fields."

        Remember, your goal is to educate and assist the user in learning AI effectively.
        """,
        model=model,
    )

    result = await Runner.run(agent, "Tell me about MCP Servers in Agentic AI", run_config=config)
    print(result.final_output)
    # Function calls itself,
    # Looping in smaller pieces,
    # Endless by design.


if __name__ == "__main__":
    asyncio.run(async_main())