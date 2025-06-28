import os
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, field_validator
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled


class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: Decimal
    total: Decimal

    @field_validator("total", mode="before")
    @classmethod
    def compute_total(cls, total, info):
        # total argument might be missing or wrong; compute from quantity & unit_price
        qty = info.data.get("quantity")
        price = info.data.get("unit_price")
        return qty * price

class Invoice(BaseModel):
    invoice_id: str
    date: str  # you could use datetime with a parser if desired
    bill_to: str
    items: List[LineItem]
    subtotal: Decimal
    tax: Decimal
    total: Decimal

    @field_validator("total", mode="before")
    @classmethod
    def compute_grand_total(cls, total, info):
        subtotal = info.data.get("subtotal")
        tax = info.data.get("tax")
        return subtotal + tax


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = AsyncOpenAI(api_key=GEMINI_API_KEY,base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)


# Agent setup
agent = Agent(
    name="InvoiceParser",
    instructions=(
        "You receive a scanned invoice text. Extract a JSON object matching the Invoice schema: "
        "invoice_id, date, bill_to, a list of items, and compute subtotal, tax, and total."
    ),
    model=model,
    output_type=Invoice,
)

# Example invoice text
invoice_text = """
Invoice #12345
Date: 2025-06-10
Bill To: Acme Corp.

Items:
Widget A — 2 @ $10.50 each
Widget B — 5 @ $3.20 each

Tax (8%): $4.96
"""

# Run the agent
result = Runner.run_sync(agent, invoice_text)
invoice: Invoice = result.final_output

# Output
print("Invoice parsed successfully:")
print(invoice)
print("\nInvoice Items:")

print(invoice.items)
print("\nInvoice Details:")
