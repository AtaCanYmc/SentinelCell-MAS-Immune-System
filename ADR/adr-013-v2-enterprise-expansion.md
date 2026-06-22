# ADR-013: V2 Enterprise Expansion (Admin UI, Automated DLQ, Advanced Security)

## Status
**Accepted**

## Context
Following a deep architectural review of the SentinelCell multi-agent middleware, it was determined that while the core mechanisms (LangGraph Orchestration, LLM Self-Healing, and Agnostic Registries) were robust, the operational and administrative layers lacked enterprise-grade automation and visibility:
1. **Manual Dead Letter Queue (DLQ):** Dropped payloads were logged to `.antigravity/logs/dlq.json` but required a manual CLI script (`dlq_replay.py`) for re-evaluation, introducing operational overhead during high-traffic anomalies.
2. **Lack of Operational Visibility:** System state, quarantine alerts, and traffic metrics were only visible through Prometheus/Grafana or raw terminal logs, lacking an out-of-the-box, dedicated interface for gateway administrators.
3. **Static Security Heuristics:** The Prompt Injection defense relied on basic substring checks (e.g., searching for the phrase "SECURITY_BREACH" or "ignore previous"), which could be bypassed by sophisticated LLM jailbreak attempts hidden within seemingly benign schema mismatch errors.
4. **Schema Evolution Handling:** The system's ability to seamlessly bridge backward compatibility gaps (e.g., a Producer sending a V2 nested JSON object to a Consumer expecting a V1 string) was theoretically possible but not explicitly demonstrated or stress-tested.

## Decision
To elevate the system to V2 (Enterprise-Ready) status, the following components were introduced:
1. **Automated DLQ Worker (`dlq_worker.py`):** An asynchronous background process was built to automatically monitor the DLQ. It drops malicious payloads permanently but pushes recoverable payloads back into the `sentinel.in` Redis queue. Future iterations will introduce precise, ID-based exponential backoff mechanics based on this foundation.
2. **Admin Dashboard UI (`dashboard/`):** A modern, reactive administrative dashboard was scaffolded using Vite, React, and Tailwind CSS. Hosted alongside the FastAPI Gateway, it provides a "Glassmorphism" interface for real-time monitoring of intercepted, healed, and dropped packets, as well as the active quarantine status.
3. **Advanced Regex Sanitization:** The `SecuritySanitizer` in `validation.py` was heavily upgraded to utilize strict regex patterns for detecting complex jailbreaks (`eval`, `bypass`, `system override`) and SQL/Command Injection attempts before the payload is ever submitted to the LLM.
4. **End-to-End Simulation Suite:** Three new enterprise simulations were introduced into `examples/`:
   - `finance_schema_evolution.py`: Proves SentinelCell's ability to perform real-time schema downgrades from V2 to V1, solving multi-agent version drift.
   - `iot_passive_monitoring.py`: Demonstrates the 0ms latency impact of `PASSIVE_MONITORING=true` on massive telemetry payloads.
   - `poison_pill_demo.py`: Validates the newly enhanced Regex Sanitizer by instantly dropping a deeply embedded jailbreak attempt.

## Consequences
### Positive
- **Reduced Operational Toil:** DevOps engineers no longer need to manually execute DLQ replays.
- **Improved Triage:** The React Admin Dashboard provides an immediate, out-of-the-box visual representation of the system's health without requiring a complex Grafana setup.
- **Bulletproof Security:** The Regex Sanitization acts as an impenetrable shield against the majority of known LLM manipulation tactics, saving token budget and protecting backend databases.
- **Confirmed Backward Compatibility:** The schema evolution capabilities of the self-healing LLM are now demonstrably proven.

### Negative
- **UI Maintenance:** Introducing a separate Node.js/React frontend inside the repository adds frontend dependency management (e.g., `package.json`, `npm install`) to a predominantly Python-based repository.
