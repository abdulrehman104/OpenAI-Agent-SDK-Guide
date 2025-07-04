import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, WebSearchTool, FileSearchTool

load_dotenv()

agent = Agent(
    name="Assistant",
    tools=[
        WebSearchTool(),
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["vs_6813268d82a081919782a0990f3a68f9"],
            # vector_store_ids=["VECTOR_STORE_ID"],
        ),
    ],
)


async def main():
    result = await Runner.run(agent, "Show Muhammad Qasim current organization and job title")
    return result.final_output

if __name__ == "__main__":
    asyncio.run(main())

    # Example usage: asyncio.run(main("latest advancements in AI"))
    # You can replace the topic with any other topic of interest.
    # Note: Ensure you have the necessary environment variables set for the web search tool to function.
