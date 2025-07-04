import os
from pydantic import BaseModel
from dataclasses import dataclass
from typing import TypedDict, List
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled


# ———— Gemini API Key & Client Setup ————————————————————————————————
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = AsyncOpenAI(api_key=GEMINI_API_KEY,base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)


# ———— Basic Pydantic Model Example: ————————————————————————————————
class SumResult(BaseModel):
    result: int

agent = Agent(
    name="Adder",
    instructions="Add two numbers and return JSON with `result`.",
    model=model,
    output_type=SumResult
)
result = Runner.run_sync(agent, "Add 8 and 5.")
print(f"Result: {result.final_output}")  # Output: Result: 13


# ———— Dataclass Support: ————————————————————————————————
@dataclass
class Greet:
    greeting: str

agent = Agent(
    name="Greeter",
    instructions="Return a greeting in JSON `{greeting: ...}`.",
    model=model,
    output_type=Greet
)
output = Runner.run_sync(agent, "Say hello.").final_output
print(f"Greeting: {output.greeting}")  # Output: Greeting: Hello!


# ———— TypedDict: ————————————————————————————————
class Weather(TypedDict):
    city: str
    temperature: float

agent = Agent(
    name="WeatherFetcher",
    instructions="Return JSON with `city` and numeric `temperature`.",
    model=model,
    output_type=Weather
)

output = Runner.run_sync(agent, "Weather in Berlin?")
print(output.final_output)  # Output: {'city': 'Berlin', 'temperature': 20.5}

# ———— List of Models: ————————————————————————————————

class Task(BaseModel):
    id: int
    description: str

agent = Agent(
    name="TaskLister",
    instructions="List three tasks as JSON array of objects `{id, description}`.",
    model=model,
    output_type=List[Task]
)
tasks = Runner.run_sync(agent, "Give me three chores.")
print("Tasks:")
for task in tasks.final_output:
    print(f"- {task.id}: {task.description}")


# ———— Nested Models: ————————————————————————————————
class Attendee(BaseModel):
    name: str
    rsvp: bool

class Event(BaseModel):
    title: str
    attendees: List[Attendee]

agent = Agent(
    name="EventPlanner",
    instructions="Return JSON with `title` and list of `attendees` (name + rsvp).",
    model=model,
    output_type=Event
)
ev = Runner.run_sync(agent, "Create an event 'Meeting' with two attendees.").final_output
print(f"Event: {ev.title}")
for attendee in ev.attendees:
    print(f"- {attendee.name} (RSVP: {'Yes' if attendee.rsvp else 'No'})")