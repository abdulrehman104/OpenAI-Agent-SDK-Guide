import os
import asyncio
import requests
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, List
from dataclasses import dataclass
from agents import Agent, Runner, function_tool, set_tracing_disabled, AsyncOpenAI, OpenAIChatCompletionsModel

load_dotenv()

# Get API key from environment variables
WEATHER_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("WEATHER_API_KEY:", WEATHER_API_KEY)
print("GEMINI_API_KEY:", GEMINI_API_KEY)

client = AsyncOpenAI(api_key=GEMINI_API_KEY,base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)


@dataclass
class WeatherInfo:
    temperature: float
    feels_like: float
    humidity: int
    description: str
    wind_speed: float
    pressure: int
    location_name: str
    rain_1h: Optional[float] = None
    visibility: Optional[int] = None


@function_tool
def get_weather(lat: float = 24.8610, lon: float = 67.0099) -> str:
    """Get the current weather for a specified location using OpenWeatherMap API.

    Args:
        lat: Latitude of the location (-90 to 90)
        lon: Longitude of the location (-180 to 180)
    """

    # Build URL with parameters
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract weather data from the response
        weather_info = WeatherInfo(
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            humidity=data["main"]["humidity"],
            description=data["weather"][0]["description"],
            wind_speed=data["wind"]["speed"],
            pressure=data["main"]["pressure"],
            location_name=data["name"],
            visibility=data.get("visibility"),
            rain_1h=data.get("rain", {}).get("1h"),
        )

        # Build the response string
        weather_report = f"""
       Weather in {weather_info.location_name}:
       - Temperature: {weather_info.temperature}°C (feels like {weather_info.feels_like}°C)
       - Conditions: {weather_info.description}
       - Humidity: {weather_info.humidity}%
       - Wind speed: {weather_info.wind_speed} m/s
       - Pressure: {weather_info.pressure} hPa
       """
        return weather_report

    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"


# Create a weather assistant
weather_assistant = Agent(
    name="Weather Assistant",
    instructions="""You are a weather assistant that can provide current weather information.
  
   When asked about weather, use the get_weather tool to fetch accurate data.
   If the user doesn't specify a country code and there might be ambiguity,
   ask for clarification (e.g., Paris, France vs. Paris, Texas).
  
   Provide friendly commentary along with the weather data, such as clothing suggestions
   or activity recommendations based on the conditions.
   """,
    model=model,
    tools=[get_weather]
)


async def main():

    simple_request = await Runner.run(weather_assistant, "What are your capabilities?")

    request_with_location = await Runner.run(weather_assistant, "What's the weather like in Karachi right now?")

    print(simple_request.final_output)
    print("-"*70)
    print(request_with_location.final_output)

if __name__ == "__main__":
    asyncio.run(main())
