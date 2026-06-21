# SentinelCell: Deployment Strategies

SentinelCell features a **Hybrid Deployment Architecture**. We recognize that every multi-agent system has different constraints. Whether it's a tight integration via Middleware Mode for maximum performance or a transparent Guardian Mode for legacy system protection, SentinelCell adapts to the environment. This makes it the most versatile middleware solution in the MAS ecosystem.

SentinelCell is designed to be deployment-agnostic. You can integrate it into your system using one of two modes:

## 1. Middleware Mode (SDK Approach)
**Best for:** Tight integration, low-latency agentic loops, and direct method calls.
- **How:** Import `SentinelCell` as a library and call the `intercept()` method directly from your producer code.
- **Benefit:** No extra network hop; the agent logic runs inside the same process as your producer/consumer.

## 2. Guardian Mode (Gateway/Proxy Approach)
**Best for:** Existing systems, black-box legacy agents, and centralized traffic monitoring.
- **How:** Deploy SentinelCell as a `FastAPI` gateway. Redirect all agent traffic (HTTP/JSON) through the Gateway endpoint.
- **Benefit:** Zero code changes in your existing agents; central auditing and security enforcement.
