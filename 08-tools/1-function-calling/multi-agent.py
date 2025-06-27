import os
import requests
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, set_tracing_disabled, AsyncOpenAI, OpenAIChatCompletionsModel

# Load environment variables from .env file
load_dotenv()


# Get Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("GEMINI_API_KEY:", GEMINI_API_KEY)


# Initialize the OpenAI-compatible Gemini client
client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)


# Define a function tool to fetch weather information
@function_tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a given city using WeatherAPI.
    Returns the temperature and weather condition.
    """
    response = requests.get(
        f"http://api.weatherapi.com/v1/current.json?key=8e3aca2b91dc4342a1162608252604&q={city}"
    )
    data = response.json()
    return (
        f"The current weather in {city} is {data['current']['temp_c']}°C "
        f"with {data['current']['condition']['text']}."
    )


# Define a function tool to find a PIAIC student by roll number
@function_tool
def student_finder(student_roll: int) -> str:
    """
    Find the PIAIC student based on the roll number.
    Each student has details like name, program, batch, and email.
    """
    # Simulated student database
    data = {
        1: {"name": "Muhammad Qasim", "program": "AI", "batch": "Batch 1", "email": "qasim@piaic.org"},
        2: {"name": "Zia Khan", "program": "Blockchain", "batch": "Batch 1", "email": "zia@piaic.org"},
        3: {"name": "Daniyal Nagori", "program": "Cloud Native", "batch": "Batch 2", "email": "daniyal@piaic.org"},
        4: {"name": "Fatima Khalid", "program": "AI", "batch": "Batch 3", "email": "fatima.khalid@example.com"},
        5: {"name": "Ahmed Raza", "program": "Web 3.0", "batch": "Batch 2", "email": "ahmed.raza@example.com"},
        6: {"name": "Ayesha Khan", "program": "Cloud Native", "batch": "Batch 4", "email": "ayesha.khan@example.com"},
        7: {"name": "Bilal Iqbal", "program": "GenAI", "batch": "Batch 5", "email": "bilal.iqbal@example.com"},
        8: {"name": "Sara Nadeem", "program": "AI", "batch": "Batch 4", "email": "sara.nadeem@example.com"},
        9: {"name": "Usman Tariq", "program": "Blockchain", "batch": "Batch 3", "email": "usman.tariq@example.com"},
        10: {"name": "Hina Aslam", "program": "Web 3.0", "batch": "Batch 5", "email": "hina.aslam@example.com"},
        11: {"name": "Zaid Ali", "program": "GenAI", "batch": "Batch 2", "email": "zaid.ali@example.com"},
        12: {"name": "Maryam Shah", "program": "AI", "batch": "Batch 6", "email": "maryam.shah@example.com"},
        13: {"name": "Imran Qureshi", "program": "Cloud Native", "batch": "Batch 3", "email": "imran.qureshi@example.com"},
        14: {"name": "Noor Fatima", "program": "AI", "batch": "Batch 5", "email": "noor.fatima@example.com"},
        15: {"name": "Hamza Yousuf", "program": "Web 3.0", "batch": "Batch 4", "email": "hamza.yousuf@example.com"},
        # Add more students if needed
    }

    # Get student details based on roll number
    student = data.get(student_roll)

    # Return formatted details or not found message
    if student:
        return (
            f"Name: {student['name']}\n"
            f"Program: {student['program']}\n"
            f"Batch: {student['batch']}\n"
            f"Email: {student['email']}"
        )
    else:
        return "Student Not Found"


# Create the agent with custom instructions
agent = Agent(
    name="Assistant",
    instructions="You only respond in haikus.",  # Example instruction
    tools=[get_weather, student_finder],
    model=model
)


# Run the agent synchronously with a test prompt
result = Runner.run_sync(agent, "Share PIAIC roll no4 student details.")
result1 = Runner.run_sync(agent, "What's the weather like in Karachi?")


# Output the result
print(result.final_output)
print(result1.final_output)
