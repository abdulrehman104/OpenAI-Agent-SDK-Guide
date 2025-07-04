import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, handoff, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-1.5-flash", openai_client=client)
set_tracing_disabled(True)


# Create specialist agents
billing_agent = Agent(
    name="Billing Agent",
    instructions="""You are a billing specialist who helps customers with payment issues.
    Focus on resolving billing inquiries, subscription changes, and refund requests.
    If asked about technical problems or account settings, explain that you specialize
    in billing and payment matters only.""",
    model=model,
)

technical_agent = Agent(
    name="Technical Agent",
    instructions="""You are a technical support specialist who helps with product issues.
    Assist users with troubleshooting, error messages, and how-to questions.
    Focus on resolving technical problems only.""",
    model=model,
)


async def main(promot):
    print(f"Processing inquiry: \n{promot}\n")

   # Create a triage agent that can hand off to specialists
    triage_agent = Agent(
        name="Customer Service",
        instructions="""You are the initial customer service contact who helps direct
        customers to the right specialist.
        
        If the customer has billing or payment questions, hand off to the Billing Agent.
        If the customer has technical problems or how-to questions, hand off to the Technical Agent.
        For general inquiries or questions about products, you can answer directly.
        
        Always be polite and helpful, and ensure a smooth transition when handing off to specialists.""",
        model=model,
        # Direct handoff to specialist agents
        handoffs=[billing_agent, technical_agent],
    )
    
    print(f"Created triage agent: \n{triage_agent.name}\n")

    result = await Runner.run(triage_agent, promot)
    print(f"Final output:\n{result.final_output}\n")



if __name__ == "__main__":

    # Example customer inquiries
    billing_inquiry = "I was charged twice for my subscription last month. Can I get a refund?"
    technical_inquiry = "The app keeps crashing when I try to upload photos. How can I fix this? Give me the shortest solution possible."
    general_inquiry = "What are your business hours?"

    # Process the different types of inquiries
    asyncio.run(main(billing_inquiry))
    print('--'*50)
    asyncio.run(main(technical_inquiry))
    print('--'*50)
    asyncio.run(main(general_inquiry))
    print('--'*50)
