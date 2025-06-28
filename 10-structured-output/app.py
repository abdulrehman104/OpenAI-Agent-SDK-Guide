import os
import asyncio
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled

# ———— 1. Load API Key & Initialize Gemini Client ————————————————————————————————
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"[Startup] GEMINI_API_KEY loaded: {bool(GEMINI_API_KEY)}")

client = AsyncOpenAI(api_key=GEMINI_API_KEY,base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)


# ———— 2. Define Specialist Agents ————————————————————————————————
note_taking_agent = Agent(
    name="Note Manager",
    instructions="You help users take and organize notes efficiently.",
    model=model
)

task_management_agent = Agent(
    name="Task Manager",
    instructions="You help users manage tasks, deadlines, and priorities.",
    model=model
)

calendar_agent = Agent(
    name="Calendar Manager",
    instructions="You schedule events, set reminders, and check availability.",
    model=model
)

email_agent = Agent(
    name="Email Manager",
    instructions="You draft, organize, and prioritize emails for the user.",
    model=model
)

reminder_agent = Agent(
    name="Reminder Manager",
    instructions="You send proactive reminders and follow-ups based on user tasks.",
    model=model
)


# ———— 3. Assemble Coordinator Agent ————————————————————————————————
async def main():
    # Wrap specialist agents as tools
    tools = [
        note_taking_agent.as_tool(
            tool_name="note_taking",
            tool_description="For taking, organizing, and retrieving notes"
        ),
        task_management_agent.as_tool(
            tool_name="task_management",
            tool_description="For managing tasks, deadlines, and tracking priorities"
        ),
        calendar_agent.as_tool(
            tool_name="calendar_management",
            tool_description="For creating and checking calendar events"
        ),
        email_agent.as_tool(
            tool_name="email_management",
            tool_description="For drafting and organizing emails"
        ),
        reminder_agent.as_tool(
            tool_name="reminder_management",
            tool_description="For setting up reminders and follow-ups"
        ),
    ]

    # Coordinator instructions guide how to pick tools
    coordinator_instructions = """
        You are the Productivity Assistant. Based on the user's request:
        - Use the `note_taking` tool for note questions.
        - Use `task_management` for tasks and deadlines.
        - Use `calendar_management` for scheduling events.
        - Use `email_management` for email drafting/organization.
        - Use `reminder_management` for proactive reminders.

        Decide which tool(s) to invoke and orchestrate between them.
        Always explain which tool you chose and why.
        """

    productivity_assistant = Agent(
        name="Productivity Assistant",
        instructions=coordinator_instructions,
        model=model,
        tools=tools
    )

    # Example run
    # user_prompt = "I need to keep track of my project deadlines and follow up via email"
    user_prompt = """I need to prepare for next week’s product launch:

        - Take notes from the launch plan document
        - Add tasks for finalizing collateral and approving graphics
        - Schedule a rehearsal call on July 1st at 11 AM
        - Draft the announcement email to customers
        - Set reminders for each of these steps
    """
    result = await Runner.run(productivity_assistant, user_prompt)
    print(result.final_output)

if __name__ == "__main__":
    print("[Main] Starting async event loop...")
    asyncio.run(main())


# import os
# from decimal import Decimal
# from typing import List, Optional
# from pydantic import BaseModel, field_validator
# from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled

# class LineItem(BaseModel):
#     description: str
#     quantity: int
#     unit_price: Decimal
#     total: Decimal

#     @field_validator("total", pre=True, always=True)
#     def validate_total(cls, v, values):
#         qty = values.get("quantity")
#         price = values.get("unit_price")
#         return qty * price

# class Invoice(BaseModel):
#     invoice_id: str
#     date: str  # could parse to datetime if desired
#     bill_to: str
#     items: List[LineItem]
#     subtotal: Decimal
#     tax: Decimal
#     total: Decimal

#     @field_validator("total", pre=True, always=True)
#     def compute_grand_total(cls, v, values):
#         return values["subtotal"] + values["tax"]

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# print("Using Gemini API Key:", GEMINI_API_KEY)

# client = AsyncOpenAI(api_key=GEMINI_API_KEY,base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
# model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
# set_tracing_disabled(True)


# # Agent setup
# agent = Agent(
#     name="InvoiceParser",
#     instructions=(
#         "You receive a scanned invoice text. Extract a JSON object matching the Invoice schema: "
#         "invoice_id, date, bill_to, a list of items, and compute subtotal, tax, and total."
#     ),
#     model=model,
#     output_type=Invoice,
# )

# # Example invoice text
# invoice_text = """
# Invoice #12345
# Date: 2025-06-10
# Bill To: Acme Corp.

# Items:
# Widget A — 2 @ $10.50 each
# Widget B — 5 @ $3.20 each

# Tax (8%): $4.96
# """

# result = Runner.run_sync(agent, invoice_text)
# invoice: Invoice = result.final_output

# print(f"Invoice {invoice.invoice_id} for {invoice.bill_to}, total ${invoice.total}")
# for li in invoice.items:
#     print(f" - {li.quantity}×{li.description} = ${li.total}")
