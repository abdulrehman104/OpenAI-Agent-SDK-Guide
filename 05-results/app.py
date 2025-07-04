import os
from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled

# ———————————————————————————————— Setup ————————————————————————————————
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(disabled=True)


# A simple tool to demo tool calls in the result
@function_tool
def add(a: int, b: int) -> int:
    return a + b

# Create an agent that may call our add tool
agent = Agent(
    name="AdderAgent",
    instructions="Use the add tool to sum two numbers and return a JSON with the field `result`.",
    model=model,
    tools=[add],
)

# ———————————————————————————————— Run ————————————————————————————————
run_result = Runner.run_sync(agent, "Please add 7 and 5.")


# ———— Inspecting RunResult ————————————————————————————————

# 1. Results ——————> (the full RunResult object)
print("\n--- 1. Full RunResult: --- ---")
print(run_result)


# 2. Final output ——————>  As we set output_type=SumResult, final_output is a SumResult instance
print("\n--- 2. Final output: --- ---")
print(run_result.final_output)          # SumResult(result=12)


# 3. Inputs for the next turn ——————> This includes the original user prompt and all LLM/tool messages
print("\n --- 3. Inputs for next turn: --- ---")
for msg in run_result.to_input_list():
    print(msg)


# 4. Last agent ——————> If you had handoffs, this tells you which agent finished last
print("\n --- 4. Last agent: ---")
print(run_result.last_agent.name)


# 5. New items ——————> A list of RunItem objects created during this run
print("\n --- 5. New items: ---")
for item in run_result.new_items:
    print(f" - {item.__class__.__name__}: {item}")


# 6. Other information
print("\n --- 6. Other info: ---")
print("  Original input:", run_result.input)

# 7. Guardrail results
print("\n --- 7. Guardrail results: ---")
print("  Input guardrails:", run_result.input_guardrail_results)
print("  Output guardrails:", run_result.output_guardrail_results)


# 8. Raw responses ——————> Low-level LLM provider responses, including usage metadata and chunks
print("\n --- 8. Raw responses: ---")
for raw in run_result.raw_responses:
    print(f" - {raw}")


# 9. Original input
print("\n --- 9. Original input: ---")
print(run_result.input)



# Learn More About Results ——————> https://openai.github.io/openai-agents-python/ref/result/#agents.result.RunResult.last_agent
