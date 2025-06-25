# ———————————————————————————————— Imports Packages ———————————————————————————————— 
import os
from agents import set_default_openai_client, set_tracing_disabled
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")


# ————————————————————————————————  Global-Level Configuration ————————————————————————————————

external_client = AsyncOpenAI(api_key=gemini_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=external_client)
set_default_openai_client(external_client)


agent: Agent = Agent(name="Assistant", instructions="You are a helpful assistant", model=model)
result = Runner.run_sync(agent, "Hello, how are you.")

print(result.final_output)

# ————————————————————————————————  Agent-Level Configuration ————————————————————————————————

client = AsyncOpenAI(api_key=gemini_api_key,base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
set_tracing_disabled(disabled=True)

agent = Agent(
    name="Assistant",
    instructions="You only respond in haikus.",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
)

result = Runner.run_sync(agent, "Hey, Whats your name?")
print(result.final_output)

# ————  Run-Level Configuration ————————————————————————————————

external_client = AsyncOpenAI(api_key=gemini_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=external_client)
config = RunConfig(model=model, model_provider=external_client, tracing_disabled=True)

agent: Agent = Agent(name="Assistant", instructions="You are a helpful assistant", model=model)

result = Runner.run_sync(agent, "Hello", run_config=config)
print(result.final_output)