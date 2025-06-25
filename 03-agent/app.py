# ———— Simple Agent ————————————————————————————————

import os
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig

gemini_api_key = os.getenv("GEMINI_API_KEY")

provider = AsyncOpenAI(api_key=gemini_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=provider)
config = RunConfig(model=model, model_provider=provider, tracing_disabled=True )


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

result = Runner.run_sync(agent, "Hello, Tell me what is AI?", run_config=config)

print(f"Result: {result}")
print(result.final_output)