import os
import asyncio
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, handoff, RunContextWrapper


# ———— Load environment & configure client ————————————————————————————————
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)


# ———— Define the data structure to pass during handoff ————————————————————————————————
class EscalationData(BaseModel):
   reason: str
   priority: Optional[str]
   customer_tier: Optional[str]


# ———— Handoff callback that processes the escalation data ————————————————————————————————
async def process_escalation(ctx: RunContextWrapper, input_data: EscalationData):
   print(f"[ESCALATION] Reason: {input_data.reason}")
   print(f"[ESCALATION] Priority: {input_data.priority}")
   print(f"[ESCALATION] Customer tier: {input_data.customer_tier}")


# ———— Define the Escalation Agent (specialist) ————————————————————————————————
escalation_agent = Agent(
   name="Escalation Agent",
   instructions="""You handle complex or sensitive customer issues that require
   special attention. Always address the customer's concerns with extra care and detail.""",
   model=model,
)


# ———— Define the Service Agent (orchestrator) ————————————————————————————————
service_agent = Agent(
   name="Service Agent",
   instructions="""You are a customer service agent who handles general inquiries.
  
    For complex issues, escalate to the Escalation Agent and provide:
    - The reason for escalation
    - Priority level (Low, Normal, High, Urgent)
    - Customer tier if mentioned (Standard, Premium, VIP)""",
    model=model,
    handoffs=[
        handoff(
            agent=escalation_agent,
            on_handoff=process_escalation,
            input_type=EscalationData,
        )
    ],
)


# ———— Async entrypoint & execution ————————————————————————————————
async def main():
    result = await Runner.run(service_agent, "A customer has a billing issue that requires special attention. Please escalate this to the Escalation Agent with the following details:\n\n- Reason: Billing dispute\n- Priority: High\n- Customer tier: Premium")
    print("Agent output:", result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
