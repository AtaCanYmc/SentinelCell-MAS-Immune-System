# SentinelCell Logging Policy

## Purpose

To maintain a transparent audit trail of all agentic decisions, self-healing actions, and security-critical events
within the SentinelCell ecosystem.

## Log Categories

- **[SYSTEM]:** Infrastructure, sandbox initialization, and service status.
- **[AGENT]:** Agentic reasoning, decision-making, and state transitions.
- **[SECURITY]:** Antigravity sandbox execution logs, access violations, and validation results.
- **[ERROR]:** Exceptions, failed validations, and aborted commits.

## Log Format (Structured JSON)

All logs MUST be stored as structured JSON to allow for easy querying:

```json
{
  "timestamp": "ISO-8601",
  "level": "INFO|WARN|ERROR",
  "category": "SYSTEM|AGENT|SECURITY",
  "decision_id": "uuid-v4",
  "message": "Human-readable description",
  "metadata": {
    "agent_id": "...",
    "skill": "..."
  }
}
```

## Storage Strategy

- **Primary:** `logs/agent_decisions.json` (Structured, machine-readable).
- **Secondary:** `logs/system.log` (Text-based, human-readable).
- **Retention:** Logs are rotated daily. Critical security logs are archived in `logs/archives/`.

## Log Integrity & Security

- **Tamper-Evident Logs:** Every log entry is assigned a cryptographic `checksum` (SHA-256). This hash is generated
  based on the entry's content, ensuring that the audit trail remains immutable and any unauthorized modification to the
  logs can be instantly detected.
- **Emergency Shutdown Procedure:**
    - If the system detects that `SECURITY` category errors exceed 5 incidents within a 60-second window, it
      automatically enters **"Sentinel Quarantine Mode"**.
    - **Quarantine Actions:**
        - The `Antigravity` sandbox immediately terminates all external network connections.
        - The `auto-commit` capability for all agents is instantly revoked.
        - A high-priority `CRITICAL` alert is dispatched to the system administrator dashboard.
        - Manual intervention and a cryptographic verification of the logs are required to lift the quarantine.

## Agent Responsibilities

1. **Decision Traceability:** Before any `auto-commit` is initiated, the agent MUST log the specific `decision_id` and a
   `reasoning_summary` into the `agent_decisions.json` file.
2. **Sandbox Execution Context:** Every action executed within the `Antigravity` sandbox MUST be logged with its full
   execution context, including the input payload, the applied repair logic, the sandbox exit code, and the final
   verification status.
3. **Log Rotation:** The system ensures that all logs are rotated daily at 00:00 UTC to maintain optimal performance and
   prevent disk space exhaustion in the production environment.

### Implementation Tip: `src/core/logger.py`

To make this policy "real," you should implement a simple logger in your `src/core/logger.py`.
