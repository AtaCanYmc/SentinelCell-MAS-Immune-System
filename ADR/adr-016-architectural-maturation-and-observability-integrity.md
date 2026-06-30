# ADR-016: Architectural Maturation & Observability Integrity

| Metadata | Details |
| :--- | :--- |
| **Date** | 2026-06-30 |
| **Status** | `Accepted` |
| **Author** | SentinelCell Core Architects |
| **Deciders** | Technical Committee & Architecture Board |
| **Relations** | Amends [ADR-001](adr-001-langgraph-orchestrator.md), [ADR-002](adr-002-mcp-registry.md), [ADR-007](adr-007-real-time-observability.md) |

## Context

Following security reviews and load-testing audits of the V3 architecture, several critical reliability, performance, and security issues were identified:
1. **Circuit Breaker Runtime Crash:** Mismatches between dictionary-based state and legacy integer checks crashed the API health status endpoints.
2. **Event Loop Blocking I/O:** The self-healing loop utilized synchronous Redis clients, and the Outbox worker called synchronous database/embedding client methods directly. Similarly, log sinks executed blocking file/network writes. This choked asynchronous performance.
3. **Dynamic Rule Vulnerability:** Dynamic validator skills utilized Python's built-in `eval()`, exposing the system to Remote Code Execution (RCE) via manipulated configurations.
4. **Subprocess Overhead:** The Schema Registry Client spawned fresh Python subprocesses for every single MCP server connection.
5. **Observability Blindspot:** Major sections of the codebase bypassed the custom `AgnosticLogger` and printed directly to `rich.Console()`, preventing logs from reaching File/Elasticsearch sinks.

## Decision

We designed and executed a multi-phase architectural maturation process to secure the system and restore full logging routing:

1. **Non-Blocking Execution (I/O Offloading):**
   - Converted all semantic cache and rate-limiting Redis calls to use `redis.asyncio` with async context managers.
   - Wrapped synchronous database and embedding writes in `asyncio.to_thread` executors.
   - Refactored `AgnosticLogger.print` to offload blocking print fanouts to thread executors (`run_in_executor`) or background threads.

2. **Secure Rule Evaluation (AST Parser):**
   - Removed all `eval()` calls. Introduced `safe_eval()` utilizing Python's `ast` (Abstract Syntax Tree) module to safely evaluate logic conditions without executing arbitrary bytecode.

3. **Persistent MCP Connection:**
   - Redesigned `SchemaRegistryClient` to maintain a single persistent stdio session and bound its lifecycle directly to the FastAPI lifecycle events (lifespan start/stop callbacks).

4. **Observability & Log Routing Integrity:**
   - Refactored all direct `rich.Console` instantiations to fetch and print via the unified `AgnosticLogger`. All decision and system logs are now fully captured by our file and Elasticsearch sinks.

## Consequences

### Positive
- **Observability:** Complete log routing visibility. Sinks capture 100% of internal decisions.
- **Resource Efficiency & Latency:** Persistent MCP subprocesses reduce schema fetch latencies by ~100-300ms. Non-blocking Redis/database operations prevent main event loop starvation.
- **Security:** Complete mitigation of RCE risks in dynamic rules.

### Negative
- **Trace Complexity:** Lifespan startup hooks must execute properly for the persistent subprocesses to launch successfully.
