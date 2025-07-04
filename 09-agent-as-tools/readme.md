# **Agents as Tools:**

## **What is Agents as Tools:**

The Agents SDK allows you to use agents themselves as tools, enabling a hierarchical structure where specialist agents work under a coordinator. This is a powerful pattern for complex workflows.

## **How It Works**

1. Convert an Agent into a Tool

   - Call .as_tool(tool_name, tool_description) on an existing Agent instance.
   - This produces a FunctionTool-like wrapper that, when invoked, runs the sub-agent and returns its final
     output as a string.

2. Register in the Coordinator

   - Pass these tool-agents into the coordinator agent’s tools list.
   - In the coordinator’s instructions, refer to each tool by its tool_name.

3. Runtime Invocation

   - When the parent agent’s LLM reasoning emits a JSON payload naming one of these tools, the SDK runs the corresponding sub-agent under the hood (via Runner.run), captures its final_output, and feeds it back into the parent’s context.

## **Basic Code Example**

```py
import asyncio
from agents import Agent, Runner

# Specialist agents
spanish_agent = Agent(
    name="Spanish agent",
    instructions="You translate the user's message to Spanish",
)

french_agent = Agent(
    name="French agent",
    instructions="You translate the user's message to French",
)

# Coordinator agent using specialists as tools
orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        "You are a translation agent. "
        "Use the tools given to you to translate user messages."
    ),
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate the user's message to Spanish",
        ),
        french_agent.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate the user's message to French",
        ),
    ],
)

async def main():
    result = await Runner.run(
        orchestrator_agent,
        input="Say 'Hello, how are you?' in Spanish and French."
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

The coordinator (orchestrator_agent) sees your input, decides which tool-agent to call, e.g. "translate_to_spanish", and then embeds the sub-agent’s reply into its own response

## **When to Use Agents as Tools**

- Hierarchical Workflows: A “manager” agent that delegates subtasks (translation, data lookup) to specialized agents but retains overall control.
- Coordinated Responses: Embed multiple specialist outputs into a single, synthesized reply.
- Maintain Context: The coordinator can incorporate sub-agent outputs in its reasoning, rather than completely transferring the conversation as with a handoff.
