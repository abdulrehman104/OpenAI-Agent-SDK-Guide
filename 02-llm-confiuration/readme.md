# **LLM Configuration**

Below is a breakdown of the three levels at which you can configure your LLM client in the OpenAI Agent SDK, why each exists, and guidance on when to choose one over the others.

## **1. Global-Level Configuration:**

**What it is:**

You call `set_default_openai_client(...)` once, early in your application, to wire up a single `AsyncOpenAI` (or sync) client and model that all subsequent Agents and Runs will use by default.

```python
external_client = AsyncOpenAI(api_key=…, base_url=…)
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=external_client)
set_default_openai_client(external_client)

agent = Agent(name="Assistant", instructions="…", model=model)
result = Runner.run_sync(agent, "Hello")
```

**Why it exists:**

- **Convenience:** No need to pass your client or model around everywhere.
- **Consistency:** Guarantees all agents in your process use the same endpoint, credentials, and defaults.

**When to use it:**

- In small scripts or one-off tools where you don’t need multiple credentials or model variants.
- When your entire application genuinely uses a single LLM provider/configuration.

## **2. Agent-Level Configuration:**

**What it is:**
You disable tracing or swap clients _per Agent_ by constructing each `Agent(...)` with its own `model` (backed by its own `AsyncOpenAI`), and you can call `set_tracing_disabled(True)` to turn off tracing globally—or use agent-level hooks (once available) to tune observability.

```python
client = AsyncOpenAI(api_key=…, base_url=…)
set_tracing_disabled(disabled=True)

agent = Agent(
  name="HaikuBot",
  instructions="You only respond in haikus.",
  model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
)
```

**Why it exists:**

- **Agent specialization:** Each agent can point to a different provider, model size, or set of tuning parameters.
- **Isolation:** You might want tracing on for some agents (debugging) but off for others (production).

**When to use it:**

- In multi-agent systems where different roles require different models (e.g. a “summarizer” vs. an “assistant”).
- When certain agents handle sensitive data and must disable tracing or use a compliant endpoint.

---

## 3. Run-Level Configuration

**What it is:**

You pass a `RunConfig(...)` into a specific `Runner.run_sync(agent, prompt, run_config=config)` call, temporarily overriding default or agent-level settings just for that one invocation.

```python
config = RunConfig(
  model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=external_client),
  model_provider=external_client,
  tracing_disabled=True
)
result = Runner.run_sync(agent, "Hello", run_config=config)
```

**Why it exists:**

- **Flexibility:** Swap out models or toggle tracing on a per-call basis without touching your agent definitions.
- **A/B Testing & Overrides:** Easily compare two different models or turn on verbose logging for a single run in production.

**When to use it:**

- When you need to experiment or fallback dynamically (e.g. try GPT-4 for complex questions, then GPT-3.5 if it fails).
- In serverless or request-driven contexts where each request might carry its own credentials or routing hints.

## **How to Choose Between Them:**

| Requirement                                              | Configuration Level |
| -------------------------------------------------------- | ------------------- |
| **Single, uniform client/model**                         | Global-level        |
| **Multiple agents with distinct models**                 | Agent-level         |
| **Per-call overrides (experiments, fallbacks, tracing)** | Run-level           |

---

- **Start with a Global Default** if you only need one model and one key for your whole app.
- **Elevate to Agent-Level** when certain logical “bots” need specific models or observability settings.
- **Use Run-Level** when you want ad-hoc control—A/B testing, dynamic fallbacks, or temporary tracing changes—without rewriting agent code.

By layering configuration this way, the SDK gives you both _simplicity_ (a single default) and _granularity_ (per-agent or per-run tweaks) so you can scale from quick prototypes to complex, multi-agent production systems.
