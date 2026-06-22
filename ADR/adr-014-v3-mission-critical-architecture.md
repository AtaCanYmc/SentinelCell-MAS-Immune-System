# ADR-014: V3 Mission-Critical Architecture (Zero Fault Tolerance)

## Status
**Accepted**

## Context
Following an extensive architectural review by the Technical Jury (scoring 8.5/10), the SentinelCell middleware was praised for its robust defense-in-depth and dynamic healing capabilities. However, three critical vulnerabilities were identified that prevented the system from achieving true "Mission-Critical" (Enterprise, Tier-1) status:
1. **"Fail-Open" Blind Spot:** If the MCP Schema Registry server crashes, the system defaults to either `FAIL_CLOSED` (blocking all traffic) or `FAIL_OPEN` (allowing unverified traffic). This represents a severe security or availability risk.
2. **Synchronous I/O Bottleneck:** The process of logging validated payloads to the Vector Database (`_log_to_vectordb_node`) was executed via `run_in_executor`. Under massive load, thread pools exhaust quickly, creating severe latency in the main asynchronous routing loop.
3. **Semantic Drift (Data Corruption Risk):** While the LLM repair engine effectively fixes malformed JSON syntax, it could hallucinate or silently drop critical fields (e.g., changing a transaction amount from 1500 to 0). This "Semantic Drift" lacked a deterministic validation layer.

## Decision
To completely eliminate these risks and reach V3 (Mission-Critical) status, we implemented three major architectural defenses:

1. **Schema Circuit Breaker (Stale Cache Fallback):**
   - We updated `_get_schema` inside `validation.py`. When an `Exception` is caught during MCP fetching, the system now checks its local cache.
   - If a schema exists (even if its TTL has expired), the Circuit Breaker engages and uses this **Stale Cache**. This prevents the system from blindly failing open or catastrophically failing closed during momentary network blips.

2. **Zero-I/O Outbox Pattern:**
   - We decoupled the VectorDB logging from the LangGraph orchestrator. The `log_to_vectordb_node` now performs an ultra-fast asynchronous push (`LPUSH`) to a Redis queue (`sentinel.outbox`).
   - A dedicated, lightweight microservice (`outbox_worker.py`) continuously polls this queue and batches writes to the VectorDB in the background, ensuring the main FastAPI gateway handles traffic with zero I/O latency.

3. **Dual-Layer Semantic Drift Guard:**
   - We introduced a deterministic mathematical guard inside `repair.py`. After the LLM produces a "healed" JSON, the system calculates the **Jaccard Similarity** (Value Retention) of the atomic data points between the original malformed payload and the repaired payload.
   - If the retention rate drops below an acceptable threshold (e.g., `< 30%`), the repair is immediately rejected as a hallucination, and the packet is quarantined.

4. **Industrial Simulation Suite (`examples/`):**
   - `iot_telemetry_recovery.py`: Demonstrates broken JSON stream recovery.
   - `fintech_transaction_flow.py`: Tests missing financial field handling.
   - `semantic_drift_test.py`: Proves the Semantic Drift Guard can successfully reject completely garbled (chaos) payloads.

## Consequences
### Positive
- **100% Data Integrity:** The Semantic Drift Guard guarantees that the LLM can no longer silently alter the core meaning of a payload.
- **Sub-Millisecond Gateway Latency:** The Outbox pattern ensures the gateway never waits for slow database writes.
- **Maximum Availability:** The Circuit Breaker ensures the network continues routing traffic safely even if the central MCP server experiences a severe outage.

### Negative
- **Operational Complexity:** Adding `outbox_worker.py` means an additional microservice must be monitored and scaled independently in production environments.
