import os
import asyncio
from typing import List
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, field_validator
from agents import Agent, Runner, function_tool, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, ItemHelpers


# ———— ApiKey & Client Setup ————————————————————————————————
print("🔄 Loading API key and client…")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = AsyncOpenAI(api_key=GEMINI_API_KEY,
                     base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
set_tracing_disabled(True)
print("✅ AsyncOpenAI client configured, tracing disabled.")


# ———— Tools (simulated) ————————————————————————————————
@function_tool
def flight_search_tool(origin: str, destination: str, depart: str, return_date: str) -> List[dict]:
    print(
        f"[Tool: flight_search_tool] Called with {origin} → {destination}, {depart}–{return_date}")
    return [
        {"flight_no": "AI101", "price": 350.00, "airline": "AirExample"},
        {"flight_no": "EX202", "price": 420.00, "airline": "ExampleAir"},
        {"flight_no": "FL303", "price": 300.00, "airline": "FlyHigh"},
        {"flight_no": "SK404", "price": 500.00, "airline": "SkyTravel"},
        {"flight_no": "QT505", "price": 280.00, "airline": "QuickTrip"},
    ]


@function_tool
def hotel_search_tool(city: str, checkin: str, checkout: str) -> List[dict]:
    print(f"[Tool: hotel_search_tool] Called for {city}, {checkin}–{checkout}")
    return [
        {"hotel_name": "Hotel Alpha", "price_per_night": 80.00, "rating": 4.3},
        {"hotel_name": "Beta Suites", "price_per_night": 120.00, "rating": 4.7},
        {"hotel_name": "Gamma Inn", "price_per_night": 60.00, "rating": 3.9},
        {"hotel_name": "Delta Resort", "price_per_night": 200.00, "rating": 5.0},
        {"hotel_name": "Epsilon Lodge", "price_per_night": 90.00, "rating": 4.1},
    ]


@function_tool
def process_payment_tool(amount: Decimal, card_last4: str) -> dict:
    print(
        f"[Tool: process_payment_tool] Charging ${amount} to card ending {card_last4}")
    return {"status": "success", "amount_charged": amount, "transaction_id": "TXN123456"}


# ———— Structured Output Models ————————————————————————————————
print("🔄 Defining Pydantic models…")


class FlightOption(BaseModel):
    flight_no: str
    airline: str
    price: Decimal


class HotelOption(BaseModel):
    hotel_name: str
    price_per_night: Decimal
    rating: float


class BookingConfirmation(BaseModel):
    selected_flight: FlightOption
    selected_hotel: HotelOption
    total_cost: Decimal
    payment_status: str
    transaction_id: str

    @field_validator("total_cost", mode="before")
    @classmethod
    def calc_total(cls, v, info):
        print("[Model] Calculating total_cost from selected_flight and selected_hotel")
        flight = info.data["selected_flight"].price
        hotel = info.data["selected_hotel"].price_per_night
        return flight + hotel


print("✅ Using Pydantic Models.")


# ———— Specialist Agents ————————————————————————————————
print("🔄 Configuring specialist agents…")

flight_agent = Agent(
    name="FlightAgent",
    instructions="You are a flight search specialist. Use the flight_search_tool to return a list of flights.",
    model=OpenAIChatCompletionsModel(model="gemini-1.5-pro", openai_client=client),
    tools=[flight_search_tool],
    output_type=List[FlightOption]
)
print("✅ Using FlightAgent.")

hotel_agent = Agent(
    name="HotelAgent",
    instructions="You are a hotel search specialist. Use the hotel_search_tool to return a list of hotels.",
    model=OpenAIChatCompletionsModel(model="gemini-1.5-flash", openai_client=client),
    tools=[hotel_search_tool],
    output_type=List[HotelOption]
)
print("✅ Using HotelAgent.")

payment_agent = Agent(
    name="PaymentAgent",
    instructions="You are a payment specialist. Use process_payment_tool to charge the customer.",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash-lite", openai_client=client),
    tools=[process_payment_tool],
    output_type=BookingConfirmation
)
print("✅ Using PaymentAgent.")


# ———— Orchestrator Agent ————————————————————————————————
print("🔄 Configuring orchestrator agent…")

flight_tool = flight_agent.as_tool("search_flights",  "Search flights between two cities")
hotel_tool = hotel_agent.as_tool("search_hotels",   "Search hotels in a city")
payment_tool = payment_agent.as_tool("make_payment",   "Process a booking payment")

orchestrator = Agent(
    name="TravelPlanner",
    instructions=(
        "You are a travel planner. "
        "1) Call search_flights with origin, destination, depart, return_date. "
        "2) Present the cheapest option as selected_flight. "
        "3) Call search_hotels with city, checkin, checkout. "
        "4) Present the cheapest hotel as selected_hotel. "
        "5) Call make_payment with the sum of both prices and card_last4='1234'. "
        "6) Return the full booking confirmation JSON."
    ),
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[flight_tool, hotel_tool, payment_tool],
    output_type=BookingConfirmation
)
print("✅ Orchestrator (TravelPlanner) configured.")


# ———— Streaming Interaction ————————————————————————————————
async def main(origin, destination, depart, return_date):
    try:
        print(f"\n Running travel planner for {origin} → {destination}")
        user_input = (
            f"I want to book a trip from {origin} to {destination} "
            f"departing {depart} and returning {return_date}."
        )

        result_stream = Runner.run_streamed(orchestrator, input=user_input)

        async for event in result_stream.stream_events():
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

    except Exception as e:
        print("\n❌ Error during execution:", str(e))
        raise

if __name__ == "__main__":
    asyncio.run(main(origin="Karachi", destination="Dubai", depart="2025-08-15", return_date="2025-08-20"))
