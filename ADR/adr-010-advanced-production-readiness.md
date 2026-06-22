# ADR-010: Advanced Production-Readiness (DLQ, Async I/O & Rate Limits)

## Status
**Accepted**

## Context
Positioning the project as an enterprise-standard Gateway/Middleware necessitated managing bottlenecks and potential cost losses under high traffic:
1. **Async I/O (Blocking):** While the SentinelOrchestrator LangGraph nodes were executing, the `log_to_vectordb` node ran synchronously. Any delay in the database blocked the main flow.
2. **Lack of DLQ:** Unrecoverable or dropped packets were printed to the console and permanently lost. These packets should be analyzed in a "Dead Letter Queue" (DLQ).
3. **Cost and Size Limits:** Sending malformed JSON data of unlimited size to the LLM (Large Language Model) for repair caused massive bills or Rate Limit blocks on token-based providers.
4. **Prompt Boundary Bypass:** A malicious payload carrying the `---END UNTRUSTED DATA---` tag we placed for Prompt Injection defense could bypass the boundary and infiltrate the LLM.
5. **Circuit Breaker Metrics:** Keeping the quarantine state in Redis was insufficient; it also needed to be exported for setting up alarms on Grafana dashboards.

## Decision
To make the system resilient against high-load traffic:
1. **Async I/O:** The log writing operation in `log_to_vectordb_node` was moved to a "fire-and-forget" background thread using `asyncio.get_event_loop().run_in_executor()` to prevent blocking the Event Loop.
2. **DLQ (Dead Letter Queue):** A `_log_to_dlq()` helper method was written for all rejected and oversized packets, and errors began being written to the `.antigravity/logs/dlq.json` file.
3. **Max Payload Size:** A 10,000-character `MAX_PAYLOAD_SIZE` (supported by env vars) limit was added to `orchestrator.py`. Packets exceeding the limit are dropped directly to the DLQ without reaching the LLM, providing cost protection.
4. **Prompt Sanitization:** In `repair.py`, any `---START UNTRUSTED DATA---` or `END` tags inside the raw data are replaced with `[REDACTED_BOUNDARY]` (sanitization), preventing prompt boundary bypass.
5. **Gauge Metric:** A `sentinelcell_quarantine_status` Gauge metric was created for the quarantine state, exposing the real-time `1.0` (quarantined) or `0.0` (healthy) status to Prometheus.
6. **Python GIL Note:** The reality that a Python-based Middleware/Gateway could slow down under very high traffic due to the Global Interpreter Lock (GIL) was recorded. Therefore, moving the services behind the Gateway to a passive sniffing mode or placing a Rust-based load balancer in front of it will be evaluated in the future (V2).

## Consequences
### Positive
- **High Performance:** Even if the VectorDB slows down, the main packet traffic never slows down (Non-blocking I/O).
- **Cost Control:** Unlimited token consumption and unnecessary LLM calls are completely stopped.
- **Lossless Analysis:** Thanks to the DLQ, cyber threat analysis can be performed on rejected packets later.
- **Visual Alarms:** Large red quarantine warnings can be added to Grafana.

### Negative
- **Potential Data Loss:** In the "fire-and-forget" logging mechanism, if the VectorDB is momentarily down, logs may be silently lost (this risk is accepted to preserve the main flow).
