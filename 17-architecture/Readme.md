

## 1. High‑Level Architecture Diagram

```
┌─────────────────────────┐      stream        ┌─────────────┐
│ Client / Application    │───────────────────▶│ MCP Server  │
└─────────────────────────┘                    └─────────────┘
           │                                          │
           │ calls run()                              │ forwards
           ▼                                          │
┌─────────────────────────────────────────────────────────────┐
│                         Core Orchestration                │
│                                                             │
│  ┌───────────────────┐     ┌─────────────────────────────┐  │
│  │ Runner & Agent    │◀────┤ Agent Definition            │  │
│  │     Loop          │     └─────────────────────────────┘  │
│  └───────────────────┘               ▲  ▲   ▲   ▲            │
│      ▲       ▲       ▲               │  │   │   │            │
│      │       │       │               │  │   │   │            │
│      │       │       └───────────────┘  │   │   │            │
│ calls│       │execute tool output        │   │   │            │
│  LLM │       │                            │   │   │ runs       │
│      ▼       ▼                            ▼   │   │ guardrails │
│  ┌─────────┐┌────────────┐   ┌────────────┐ │   │   │            │
│  │ Model   ││ Tool       │   │ Handoff    │ │   │   │            │
│  │Provider ││ Invocation │   │ Manager    │ │   │   │            │
│  └─────────┘└────────────┘   └────────────┘ │   │   │            │
│      ▲                       ┌────────────┐ │   │   │            │
│      │                       │ Guardrail  │ └───┘   │            │
│      │                       │ Engine     │         │            │
│      │                       └────────────┘         │            │
│      │                       ┌────────────┐         │            │
│      └──────────────────────▶│ Tracing    │─────────┘            │
│                              │ Subsystem  │                      │
│                              └────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
           │                            │
           │ HTTP JSON                  │ exports spans
           ▼                            ▼
┌───────────────────┐          ┌──────────────────┐
│ External LLM APIs │          │ Tracing Backends │
└───────────────────┘          └──────────────────┘

┌──────────────────────────────┐
│ Optional “Voice Pipeline”    │
│ • STT → text                │
│ • Runner.run() with audio   │
│ • TTS output                │
│ • Voice Providers           │
└──────────────────────────────┘

```

1. **Client / Application**
   - Starts everything by calling `Runner.run()` or sending a streaming request.
   - Can be a web app, script, voice‑enabled device, or the MCP server (multi‑client protocol).
2. **Core Orchestration**
   - **Runner & Agent Loop**: the central engine that drives the “turns” of the agent.
   - **Agent Definition**: your domain logic—instructions, available tools, termination rules.
3. **Extension Layers**
   - **Model Provider Layer**: adapts to whichever LLM APIs you use (OpenAI, Azure, local).
   - **Tool Invocation Subsystem**: runs arbitrary tools (search, database, calculator) as called by the agent.
   - **Handoff Manager**: coordinates passing control between sub‑agents or external systems.
   - **Guardrail Engine**: enforces input/output policies (content filtering, formatting).
   - **Tracing Subsystem**: captures spans/events for observability, then exports to tracing backends (Jaeger, Datadog).
4. **Optional Features**
   - **MCP Server**: lets multiple clients share one runner instance over HTTP/SSE.
   - **Voice Pipeline**: STT → agent loop → TTS, integrating speech APIs.

---

## 2. Repository Module Diagram

```
┌────────────────────┐               ┌───────────────┐
│  Utilities &       │               │ User App      │
│    Helpers         │◀──────────────│ (App / Script)│
└────────────────────┘   calls       └───────────────┘
           │                           │
           ▼                           ▼
┌──────────────────────────────────────────────────┐
│             Core SDK Engine                     │
│ ┌──────────────────┐    ┌────────────────────┐  │
│ │ Runner & Loop    │───▶│ Agent Module       │  │
│ └──────────────────┘    └────────────────────┘  │
│     │  ▲   ▲   ▲            ▲      ▲             │
│     │  │   │   │            │      │             │
│     │  │   │   └────────────┘      │             │
│     │  │   │    execute tool       │             │
│     │  │   │                       │             │
│     │  │   └─────▶ Tools Subsystem │             │
│     │  │          (invoke tools)  │             │
│     │  │                           │             │
│     │  └─────────▶ Handoffs Subsys │             │
│     │             (handoff logic)  │             │
│     │                             ▼              │
│     └─────────────▶ Guardrails Subsystem        │
│             (input/output checks)               │
│                                                 │
└──────────────────────────────────────────────────┘
            │                     │
            │ API calls /        │ emits spans
            │ HTTP ↔ JSON        ▼
   ┌────────────────────────┐  ┌─────────────────┐
   │   OpenAI / LLM API     │  │ Tracing Backends│
   └────────────────────────┘  └─────────────────┘

┌──────────────────────────────┐
│ Optional Extensions          │
│  • Voice Pipeline            │
│  • MCP Protocol (MCP)        │
│  • Other plug‑ins            │
└──────────────────────────────┘

```

1. **User Application Layer**
   - Your Python/Node/etc. script or web service imports `Runner` and kicks off `run()`.
2. **Core SDK Engine**
   - **Runner & Loop**: same as before, but now in code modules.
   - **Agent Module**: houses your `Agent` class, tool definitions, and decision logic.
3. **Subsystems**
   - **Tools Subsystem**: a registry of callable “tools” your agent can invoke.
   - **Handoffs Subsystem**: manages multi‑step handoff flows (e.g., branching to another agent).
   - **Guardrails Subsystem**: pluggable filters and validators on inputs/outputs.
4. **Models Adapter Layer**
   - Abstracts away raw HTTP calls to OpenAI (or other LLM providers) into a consistent interface.
5. **Tracing Subsystem**
   - Embedded hooks inside the runner/agents/tools to emit spans.
   - Exports to any configured tracing backend (Zipkin, OTLP, etc.).
6. **Optional Extensions**
   - **Voice Pipeline**: merge speech‑to‑text and text‑to‑speech around your agent.
   - **MCP Protocol**: share a single runner among many clients via WebSockets or SSE.

---

### How They Fit Together

- **Diagram 1** shows you the **runtime** flow—from client request, through orchestrator, to external services, and back.
- **Diagram 2** maps that flow onto the **code structure** inside the SDK repo—how modules and packages are organized.

By reading them side‑by‑side, you can trace:

| Runtime Component    | Repo Module / Package       |
| -------------------- | --------------------------- |
| Runner & Agent Loop  | `runner.py` / `loop.py`     |
| Agent Definition     | `agents/` directory         |
| Tool Invocation      | `tools/` package            |
| Model Provider Layer | `models/adapter.py`         |
| Guardrail Engine     | `guardrails/` package       |
| Handoffs Subsystem   | `handoffs/` package         |
| Tracing Subsystem    | `tracing/` package          |
| MCP / Voice (opt.)   | `mcp/`, `voice/` extensions |

This dual view should help you both understand **how** the system runs at runtime and **where** in the code to look when you want to extend or customize any piece of it.
