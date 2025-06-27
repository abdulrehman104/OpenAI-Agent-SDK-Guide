Below is an in-depth, focused explanation of **Custom Function Tools** and the SDK’s **Automatic Argument & Docstring Parsing**, drawn directly from the official Agent SDK resources.

---

## Custom Function Tools

Custom function tools let you turn any Python function into a first-class tool an agent can call.

1. **Decorator & Registration**

   - You simply annotate a regular Python function with `@function_tool` from `agents`.
   - The decorator inspects the function’s signature and automatically generates a JSON schema for its inputs and outputs.

   ```python
   from agents import function_tool

   @function_tool
   def get_weather(city: str, units: str = "metric") -> str:
       """
       Fetches the current weather for a given city.

       Parameters:
       - city (str): Name of the city (e.g., "London").
       - units (str): Units for temperature, either "metric" or "imperial".

       Returns:
       - A human-readable string describing the weather.
       """
       # (Imagine this calls an external weather API…)
       temp = 20 if units == "metric" else 68
       return f"The weather in {city} is {temp}°{ 'C' if units=='metric' else 'F' }."
   ```

2. **Schema Generation**

   - Parameter names, types, defaults, and your docstring’s descriptions become the tool’s OpenAPI-style schema.
   - When the agent calls your tool, the SDK validates arguments (types, required fields) before invoking your function.

3. **Integration with Agents**

   - You pass your function tool into the agent’s `tools` list.
   - In the agent’s reasoning, it can choose to call `"get_weather"` with structured JSON arguments.

   ```python
   from agents import Agent, Runner

   agent = Agent(
       name="WeatherAgent",
       instructions="Use the get_weather tool to answer any weather question.",
       tools=[get_weather]
   )

   result = Runner.run_sync(agent, "What’s the weather in Tokyo in imperial units?")
   print(result.final_output)
   ```

---

## Automatic Argument & Docstring Parsing

To minimize boilerplate and ensure clear documentation, the Agent SDK automatically:

1. **Parses Function Signatures**

   - Reads each parameter’s name, type annotation, and default value.
   - Marks parameters without defaults as **required**.

2. **Extracts Docstrings**

   - Converts your function’s docstring into the `description` field for the tool and for each parameter, enhancing the LLM’s understanding of when and how to call it.

3. **Builds JSON Schema**

   - Combines signature data and docstring text into a Pydantic model under the hood.
   - Example partial schema for our `get_weather` tool:

   ```jsonc
   {
     "name": "get_weather",
     "description": "Fetches the current weather for a given city.\n\nParameters:\n- city (str): Name of the city (e.g., \"London\").\n- units (str): Units for temperature, either \"metric\" or \"imperial\".\n\nReturns:\n- A human-readable string describing the weather.",
     "parameters": {
       "type": "object",
       "properties": {
         "city": {
           "type": "string",
           "description": "Name of the city (e.g., \"London\")."
         },
         "units": {
           "type": "string",
           "description": "Units for temperature, either \"metric\" or \"imperial\".",
           "default": "metric"
         }
       },
       "required": ["city"]
     }
   }
   ```

4. **Why This Matters**

   - **Accuracy**: The LLM sees clear, machine-readable schemas, reducing hallucinated or malformed calls.
   - **Developer Ergonomics**: No manual OpenAPI specs—your Python docstrings and type hints suffice.
   - **Maintainability**: Updating your function signature or docstring automatically updates the tool’s interface.

---

With these mechanisms, you get robust, self-documenting tools for your agents with minimal extra code—letting you focus on your domain logic instead of glue code or manual schema definitions.
