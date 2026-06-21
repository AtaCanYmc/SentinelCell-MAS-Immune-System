# ADR-007: Real-Time Observability via WebSockets

## Status
**Accepted**

## Context
As an autonomous Immune System operating asynchronously via message queues, the internal state, validation results, and quarantine events of SentinelCell are opaque to human operators. Static logs are insufficient for real-time monitoring of a live Multi-Agent System.

## Decision
We implemented a **Real-Time Observability Dashboard** (`src/frontend/dashboard.html`) powered by **WebSockets** connected directly to the FastAPI Gateway.

## Rationale
1. **Live Insights**: The system broadcasts system events (Validation Success, Interception, Quarantine, LLM Repair) via the `SystemBroadcaster` directly to all connected WebSocket clients.
2. **Premium UX**: The dashboard utilizes Glassmorphism, dynamic metric cards, and a live data grid, providing Enterprise-grade visibility into the AI's decision-making process.
3. **No Polling**: WebSockets provide a persistent, low-latency, bi-directional connection, eliminating the heavy server load associated with continuous HTTP polling.

## Consequences
- **Positive**: Operators gain instant, visually intuitive feedback on the health of the MAS and the actions of the Immune System.
- **Negative**: WebSocket connections must be managed and kept alive. If the FastAPI gateway restarts, clients must implement reconnection logic (handled gracefully in the JS frontend).
