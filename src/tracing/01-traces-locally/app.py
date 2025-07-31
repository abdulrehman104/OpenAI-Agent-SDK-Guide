import asyncio
import os
from dotenv import load_dotenv
from agents import AsyncOpenAI, Agent, Runner, trace, set_default_openai_client, set_default_openai_api, set_trace_processors


# ———— Custom trace processor to collect trace data locally ————————————————————————————————
from pprint import pprint
from agents.tracing.processor_interface import TracingProcessor


class LocalTraceProcessor(TracingProcessor):
    def __init__(self):
        self.traces = []
        self.spans = []

    def on_trace_start(self, trace):
        self.traces.append(trace)
        print(f"Trace started: {trace.trace_id}")

    def on_trace_end(self, trace):
        print(f"Trace ended: {trace.export()}")

    def on_span_start(self, span):
        self.spans.append(span)
        print("*"*20)
        print(f"Span started: {span.span_id}")
        print(f"Span details: ")
        pprint(span.export())

    def on_span_end(self, span):
        print(f"Span ended: {span.span_id}")
        print(f"Span details:")
        pprint(span.export())

    def force_flush(self):
        print("Forcing flush of trace data")

    def shutdown(self):
        print("=======Shutting down trace processor========")
        # Print all collected trace and span data
        print("Collected Traces:")
        for trace in self.traces:
            print(trace.export())
        print("Collected Spans:")
        for span in self.spans:
            print(span.export())


# ———— Setup environment and OpenAI client ————————————————————————————————
load_dotenv()

base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")
gemini_api_key = os.getenv("GEMINI_API_KEY")
print(gemini_api_key, base_url, model_name)

client = AsyncOpenAI(api_key=gemini_api_key, base_url=base_url)
set_default_openai_client(client=client, use_for_tracing=True)
set_default_openai_api("chat_completions")
print("OpenAI client set up with tracing enabled.")


# ———— Set up the custom trace processor ————————————————————————————————
local_processor = LocalTraceProcessor()
set_trace_processors([local_processor])


# ———— Define the agent and run it with tracing enabled ————————————————————————————————
async def main():
    agent = Agent(name="Example Agent",
                  instructions="Perform example tasks.", model=model_name)

    with trace("Example workflow"):
        first_result = await Runner.run(agent, "Start the task")
        second_result = await Runner.run(agent, f"Rate this result: {first_result.final_output}")
        print("/n" + "="*50)
        print(f"Result: {first_result.final_output}")
        print("/n" + "="*50)
        print(f"Rating: {second_result.final_output}")
        print("/n" + "="*50)


# ———— Run the main function ————————————————————————————————

if __name__ == "__main__":
    asyncio.run(main())
