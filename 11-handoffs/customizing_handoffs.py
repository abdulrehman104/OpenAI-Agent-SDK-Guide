import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from agents import Agent, handoff, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, RunContextWrapper

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = AsyncOpenAI(api_key=GEMINI_API_KEY,
                     base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(
    model="gemini-1.5-flash", openai_client=client)
set_tracing_disabled(True)


# ———— Specialist Agents ————————————————————————————————
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

account_agent = Agent(
    name="Account Management",
    instructions="""You help customers with account-related issues such as
   password resets, account settings, and profile updates.""",
    model=model,
)


# ———— Handoff Function ————————————————————————————————
async def log_account_handoff(ctx: RunContextWrapper[None]):
    print(
        f"[LOG] Account handoff triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    # In a real app, you might log to a database or alert a human supervisor


# ———— Orchestrator Agent ————————————————————————————————
async def main(promot):
    print(f"Processing inquiry: \n{promot}\n")

    # Create a triage agent that can hand off to specialists
    triage_agent = Agent(
        name="Enhanced Customer Service",
        instructions="""You are the initial customer service contact who directs
        customers to the right specialist.w
        
        If the customer has billing or payment questions, hand off to the Billing Agent.
        If the customer has technical problems, hand off to the Technical Agent.
        If the customer needs to change account settings, hand off to the Account Management agent.
        For general inquiries, you can answer directly.""",
        model=model,
        handoffs=[
            billing_agent,  # Basic handoff
            handoff(  # Customized handoff
                agent=account_agent,
                on_handoff=log_account_handoff,  # Callback function
                tool_name_override="escalate_to_account_team",  # Custom tool name
                tool_description_override="Transfer the customer to the account management team for help with account settings, password resets, etc.",
            ),
            technical_agent,  # Basic handoff
        ],
    )

    print(f"Created triage agent: \n{triage_agent.name}\n")

    result = await Runner.run(triage_agent, promot)
    print(f"Final output:\n{result.final_output}\n")


# ———— Main Execution ————————————————————————————————
if __name__ == "__main__":
    test_prompts = [
        "I need a refund for my last payment.",
        "My screen flickers when I launch the app.",
        "How can I change my account email?",
        "What are your working hours?"
    ]

    for prompt in test_prompts:
        asyncio.run(main(prompt))
        print("-" * 50)
