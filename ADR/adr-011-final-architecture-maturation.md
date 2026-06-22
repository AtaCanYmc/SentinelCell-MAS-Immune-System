# ADR-011: Final Security & Architecture Maturation

## Status
**Accepted**

## Context
Although the project was considered production-ready, 5 extreme vulnerabilities were detected under aggressive attack scenarios and massive high-load conditions:
1. **LLM DDoS (Wallet Exhaustion):** Millions of malformed packets could be injected into the system to generate an unlimited LLM bill.
2. **MCP Bottleneck (Single Point of Failure):** When the FastMCP schema server went down, SentinelCell locked up (Fail-Closed).
3. **Latency Hurdle:** The synchronous execution of LangGraph could create an unacceptable bottleneck for systems requiring millisecond precision.
4. **Lack of DLQ Replay:** Quarantined and dropped letters (`.antigravity/logs/dlq.json`) were being saved but could not be replayed.
5. **Data Poisoning:** Packets triggering Prompt Injection alerts carried the risk of infiltrating VectorDB or causing unnecessary loops even if they couldn't be repaired.

## Decision
To bring the system to "Bullet-Proof" industrial standards, the following mechanisms were developed:
1. **Rate Limiting:** A Redis-based `LLM_RATE_LIMIT_PER_MIN` limit was added to `repair.py` (Default: 50 requests/minute). When exceeded, the LLM engine shuts down and packets are thrown directly into the trash.
2. **Fail-Open MCP:** The MCP fetch call in `validation.py` was wrapped in a `try-except` block. If MCP crashes, the system releases the flow using a "Fail-Open" policy (bypassing validation) instead of failing.
3. **Passive Monitoring:** A `PASSIVE_MONITORING=true/false` flag was added to `.env`. When active, the SentinelCell Gateway passes traffic with 0ms latency, pushing all repair/error logging operations to the background using `asyncio.create_task`.
4. **Replay Script:** `src/gateways/dlq_replay.py` was written to push (Replay) dead packets inside the `dlq.json` file that are not toxic or oversized back into the `sentinel.in` queue of `redis_mq`.
5. **Poisoning Drop:** The `decider_node` in `orchestrator.py` immediately destroys the packet with the `end` node without sending it to the repair engine the moment it catches the word `SECURITY_BREACH` in the error context.

## Consequences
### Positive
- Cyber attackers can no longer DDOS to consume your LLM token budget (Rate Limit shield).
- Agent communication does not break even if MCP crashes (Fail-Open).
- Thanks to Passive Monitoring, the Gateway can perform security analysis in the background without affecting the main system flow even by a millisecond (Zero Latency).
- Malformed packets can be replayed without data loss (DLQ Replay).

### Negative
- When Passive Monitoring is enabled, malformed or toxic packets pass into the system instantly (Detected asynchronously but not blocked). This mode is only suitable for Sniffing and should be kept disabled for Gateway (Blocking) mode.
- In a Fail-Open scenario, the system may experience "Temporary Blindness" as it loses schema validation.
