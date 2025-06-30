# **Context Management:**

Context management is how you pass extra data—beyond just the user’s prompt—into every step of an agent run. It lets you inject things like database handles, user profiles, feature flags, or any shared state your tools and guardrails might need.

## **What Is Context Management?**

- Every agent run carries not only the chat “messages” but also a context object.
- This object travels alongside tool calls, guardrails, and sub‑agents, giving them access to shared services or metadata.
- Think of it as a suitcase of things your agent and tools can reach into as they execute.

## **Scenario: Personalized Greetings:**

Imagine you’re building a “Greeting Agent” that always greets the user by name and mentions whether they’re on a free or premium plan.

1.  **Without Context:**

    - The agent only sees the words you type at the prompt.
    - If you ask “Hello!”, it answers “Hello!” back—there’s no way for it to know who you are.

2.  **With Context:**

    - Before running the agent, you bundle your user’s profile (their user ID and plan level) into a context object.

    - You start the agent run like:

      >     “Runner.run(agent, input="Hello!", context=userProfile)” where userProfile holds { userId: "alice", isPremium: false }.

3.  **How the Agent Uses It:**

    - Inside its instructions or in a small helper function, the agent pulls userProfile out of its backpack.
    - It sees userId = "alice" and isPremium = false.
    - It then composes:

      >     “Hello, Alice! Thanks for using our free tier. Upgrade anytime for more features.”

Because the context traveled with every message, the agent could tailor its response based on who “Alice” is and what plan she’s on—without hard‑coding names or plan logic into the prompt. You can extend this idea:

- Feature Flags: Toggle advanced features on or off per user.
- Database Clients: Let tools fetch or store records in your own database.
- Session Data: Remember things you asked earlier in a conversation, without embedding them into the text history.

## **How to Add Context to Your Agent:**

1. Define a Context Type (optional):
   You can use any Python object, but it helps to use a dataclass or Pydantic model for clarity:

   ```python
   from dataclasses import dataclass

   @dataclass
   class MyContext:
       user_id: str
       is_premium: bool
       db_client: Any
   ```

2. Wrap Your Run Call
   Instead of Runner.run(agent, input), use Runner.run(agent, input, context=…):

   ```python
   ctx = MyContext(user_id="abc123", is_premium=True, db_client=db_conn)
   result = Runner.run_sync(agent, "Hello!", context=ctx)
   ```

3. Access in Tools or Hooks
   In a @function_tool or guardrail, receive a RunContextWrapper that exposes .context:

   ```python
   from agents import function_tool
   from agents.run_context import RunContextWrapper

   @function_tool
   def personalized_tool(ctx_wrapper: RunContextWrapper[MyContext], prompt: str) -> str:
       ctx = ctx_wrapper.context
       if not ctx.is_premium:
           return "Upgrade to premium for this feature."
       return f"Hello, user {ctx.user_id}: {prompt}"

   ```

## **How It Works:**

- Runner packages your context alongside the message history into a RunContextWrapper.
- Whenever the SDK calls a tool, guardrail, or sub‑agent, it passes the same RunContextWrapper instance.
- Your code extracts ctx_wrapper.context to read or update shared data.

## **Types of Context:**

In the OpenAI Agent SDK, context refers to any extra information or services you make available during an agent run. There are two distinct kinds of context management:

- Local Context
- Agent/LLM Context

### **1. Local Context:**

**What it is:**

- A pure‑Python object (often a dataclass or Pydantic model) that you pass into your agent run. It travels alongside every tool call, lifecycle hook, and handoff—but it is never sent to the LLM itself.

————————————— OR

- This is represented via the RunContextWrapper class and the context property within it. The way this works is:
  - You create any Python object you want. A common pattern is to use a dataclass or a Pydantic object.
  - You pass that object to the various run methods (e.g. Runner.run(..., **context=whatever**)).
  - All your tool calls, lifecycle hooks etc will be passed a wrapper object, RunContextWrapper[T], where T represents your context object type which you can access via wrapper.context.
- The most important thing to be aware of: every agent, tool function, lifecycle etc for a given agent run must use the same type of context.
- You can use the context for things like:
  - Contextual data for your run (e.g. things like a username/uid or other information about the user)
  - Dependencies (e.g. logger objects, data fetchers, etc)
  - Helper functions

**How it works:**

1. You define a context type, for example:

   ```python
   from dataclasses import dataclass

   @dataclass
   class UserInfo:
       name: str
       uid: int
   ```

2. You pass an instance of this into Runner.run (or run_sync, run_streamed):

   ```python
   user_info = UserInfo(name="John", uid=123)
   result = Runner.run_sync(agent, "Hello!", context=user_info)
   ```

3. Any @function_tool, guardrail, or lifecycle hook declared with a RunContextWrapper[UserInfo] parameter will receive that same context:

   ```python
   from agents import function_tool
   from agents.run_context import RunContextWrapper

   @function_tool
   async def fetch_user_age(wrapper: RunContextWrapper[UserInfo]) -> str:
       return f"The user {wrapper.context.name} is 47 years old"

   ```

**Why it matters::**

- Dependency Injection: Share database handles, loggers, feature‑flags, or user metadata without globals.
- Type Safety: The SDK enforces that all tools and hooks expect the same context type you pass in.
- Isolation: Since this object isn’t serialized, you can store complex Python objects or open connections safely.

### **2. Agent/LLM Context:**

**What it is:**

- Data or information that you do expose to the LLM, so it can use that information when generating text. Because the LLM only “sees” your chat history and system prompts, you must explicitly inject any context you want it to know.

————————————— OR

- When an LLM is called, the only data it can see is from the conversation history. This means that if you want to make some new data available to the LLM, you must do it in a way that makes it available in that history. There are a few ways to do this:
  - You can add it to the Agent instructions. This is also known as a "system prompt" or "developer message". System prompts can be static strings, or they can be dynamic functions that receive the context and output a string. This is a common tactic for information that is always useful (for example, the user's name or the current date).
  - Add it to the input when calling the Runner.run functions. This is similar to the instructions tactic, but allows you to have messages that are lower in the chain of command.
  - Expose it via function tools. This is useful for on-demand context - the LLM decides when it needs some data, and can call the tool to fetch that data.
  - Use retrieval or web search. These are special tools that are able to fetch relevant data from files or databases (retrieval), or from the web (web search). This is useful for "grounding" the response in relevant contextual data.

**Four primary techniques:**

1. System Prompt (instructions):
   - Static string or a function that returns a string based on your local context.
   - Always appears at the top of the LLM’s message history.
     ```py
     def make_system_prompt(ctx, agent):
         return f"User ID: {ctx.context.uid}. You are a helpful assistant."
     agent = Agent(instructions=make_system_prompt, …)
     ```
2. Additional Messages in input:
   - You can prepend or append messages when you call Runner.run().
   - These messages are lower‑priority than instructions but still visible
     ```py
     result = Runner.run_sync(
         agent,
         input=[{"role":"system","content":"Today is 2025-07-01."}, {"role":"user","content":"Tell me the date."}]
     )
     ```
3. Function Tools:
   - Expose on‑demand context via @function_tool.
   - The LLM can decide “I need the user’s profile now” and call your tool, which reads from local context and returns a string.
     ```py
     @function_tool
     async def get_user_profile(wrapper: RunContextWrapper[UserInfo]) -> str:
         return f"Name: {wrapper.context.name}, ID: {wrapper.context.uid}"
     ```
4. Retrieval & Web Search:
   - Use built‑in tools like FileSearchTool or WebSearchTool to fetch documents or live data.
   - Those tools can be configured to draw on your own knowledge base or the internet, further grounding the agent in relevant context.

**Why it matters::**

- Grounding: Prevent hallucinations by giving the model the facts it needs.
- Dynamic Personalization: Let the LLM include user‑specific details (name, preferences) in its replies.
- Scalable Updates: Change context (e.g. current date, KPI numbers) without re‑prompting or re‑training.

### **Summary:**

- Local Context lives in your Python code and powers tools, guardrails, and hooks.
- Agent/LLM Context is the subset of data you deliberately expose to the model via prompts, messages, or callable tools.

Together, these two layers let you build agents that are both stateful and personalized (via local context) and well‑informed and grounded (via LLM context), all while keeping your code clean, testable, and secure.

## **What Is RunContextWrapper:**

A **RunContextWrapper** is just a little bundle the Agent SDK gives your tool or guardrail so it has everything it needs in one place. Think of it as a package that carries:

1. **Your Context (`.context`)**

   - The custom object you passed in (e.g. user profile, database client).

2. **Conversation History (`.input_items`)**

   - The list of messages so far (each with a `role` and `content`), so your code can see what’s been said.

3. **Agent Reference (`.agent`)**

   - The actual `Agent` instance that’s running, in case you need its name or settings.

4. **Run Settings (`.run_config`)**
   - Any overrides you passed for this specific run (model choice, timeouts, etc.).

When you write a function tool or guardrail like:

```python
def my_tool(ctx_wrap: RunContextWrapper[MyContext], arg1: str) -> str:
    # you can read:
    user = ctx_wrap.context
    history = ctx_wrap.input_items
    agent = ctx_wrap.agent
    config = ctx_wrap.run_config
    ...
```

you get all four pieces without globals or extra parameters—making your code cleaner and easier to test.

## **What Is context:**

- The actual object you passed in (e.g. MyContext instance).
- A shared, immutable or mutable bag of data that lives for the full agent run.
- Use it to store clients, credentials, request metadata, or feature toggles.

## **Benefits of Context:**

- **Dependency Injection:** No globals—tools and guardrails get what they need via ctx.wrapper.context.

- **Per‑Run Configuration:** Customize behavior per user or per request (e.g. A/B flags, tenant IDs).

- **Cleaner Code:** Tools don’t have to re‑fetch or re‑initialize clients—they reuse context.db_client.

- **Multi‑Agent Workflows:** All sub‑agents and handoffs share the same context, ensuring consistent state.

By leveraging context management, you enrich every agent run with structured, shared data—making your multi‑tool, multi‑agent applications robust, testable, and maintainable.
