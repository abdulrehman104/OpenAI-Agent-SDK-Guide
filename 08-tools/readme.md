# **Tools in the OpenAI Agent SDK:**

The OpenAI Agent SDK’s tools are first-class building blocks—predefined or custom functions—that agents can invoke during a run. Tools expand an agent’s capabilities beyond pure text generation, enabling multi-step workflows, API calls, code execution, file operations, and more.

## **1. What Is a Tool?:**

A tool is a Python object the Agent SDK exposes to your Agent. When the LLM decides it needs to perform an action—search the web, run code, generate an image—it emits a special JSON payload, and the SDK invokes the corresponding tool function. Once the tool returns, its result is fed back into the agent l

**Key points:**

- **Automatic schema:** Tools use Pydantic to validate inputs and outputs.
- **Registered by name:** Agents see each tool by its name and description.
- **Decision-making:** The LLM decides when and which tool to call, unless you force a specific tool.

## **2. Hosted Tools:**

OpenAI provides a suite of hosted tools that require no extra code—you just enable them in your agent’s configuration.

| Tool Name               | Purpose                                                                          | Example Use Case                            |
| ----------------------- | -------------------------------------------------------------------------------- | ------------------------------------------- |
| **WebSearchTool**       | The WebSearchTool lets an agent search the web.                                  | Fetch current news headlines                |
| **FileSearchTool**      | The FileSearchTool allows retrieving information from your OpenAI Vector Stores. | Find code snippets in a project directory   |
| **ComputerTool**        | The ComputerTool allows automating computer use tasks.                           | Run data transformations or calculations    |
| **CodeInterpreterTool** | The CodeInterpreterTool lets the LLM execute code in a sandboxed environment.    | Analyze a CSV, generate charts, create PPTX |
| **HostedMCPTool**       | The HostedMCPTool exposes a remote MCP server's tools to the model.              | Interactive user surveys                    |
| **ImageGenerationTool** | The ImageGenerationTool generates images from a prompt.                          | Create diagrams or marketing graphics       |
| **LocalShellTool**      | The LocalShellTool runs shell commands on your machine.                          | Automate `git` commands, system diagnostics |

Each hosted tool lives in agentsand can be imported directly:

## **3. Custom Function Tools:**

You can use any Python function as a tool. The Agents SDK will setup the tool automatically:

- The name of the tool will be the name of the Python function (or you can provide a name)
- Tool description will be taken from the docstring of the function (or you can provide a description)
- The schema for the function inputs is automatically created from the function's arguments
- Descriptions for each input are taken from the docstring of the function, unless disabled

## **5. Best Practices**

- Minimal Tool Set: Expose only the tools the agent truly needs to reduce hallucinations.
- Input Validation: Use guardrails or Pydantic schemas to sanitize tool inputs.
- Result Handling: Inspect RunResult’s new_items to log or post-process tool outputs.
- Security: Be cautious with ComputerTool and LocalShellTool—limit capabilities in production.
- Observability: Enable tracing or hook into lifecycle events to monitor tool usage patterns.

With this toolkit, your agents can seamlessly combine LLM reasoning with real-world actions—from fetching live data to executing code—enabling powerful, multi-step AI-driven applications.