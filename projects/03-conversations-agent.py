import os
import asyncio
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled


# ─── 0. SET UP YOUR GEMINI CLIENT & TRACING ────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

client = AsyncOpenAI(api_key=GEMINI_API_KEY,
                     base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
set_tracing_disabled(disabled=True)


# ─── 1. DEFINE YOUR AGENT ─────────────────────────────────────────────────────────────
assistant_agent = Agent(
    name="Assistant",
    instructions="You are a concise assistant.",
    model=OpenAIChatCompletionsModel(
        model="gemini-2.0-flash", openai_client=client),
)


# ─── 2. MAIN ASYNC WORKFLOW ───────────────────────────────────────────────────────────
async def main():
    history = []  # Will accumulate the entire chat history

    while True:
        # 1. Get user input
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            break

        # 2. Append user message to history
        history.append({"role": "user", "content": user_input})

        # 3. Run the agent on the current history
        res = await Runner.run(assistant_agent, history)

        # 4. Print agent reply and append it to history
        reply = res.final_output
        print("Assistant:", reply)
        history.append({"role": "assistant", "content": reply})

    # 5. After exiting, print the full conversation
    print("\n=== Full Conversation ===")
    for msg in history:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        print(f"{role}: {content}")

if __name__ == "__main__":
    asyncio.run(main())
