# ADR-012: Dynamic Configuration and Fail-Closed Security Policy

## Status
**Accepted**

## Context
Following a DevOps and Cybersecurity review, several hardcoded limits and architectural vulnerabilities were identified that could compromise the "Guardian Mode" under severe conditions:
1. **"Fail-Open" Vulnerability:** If the MCP Schema Server crashes or is DoS'ed, the system bypassed validation to keep traffic flowing. A compromised MCP could thus allow malicious payloads to slip through completely unchecked.
2. **Hardcoded Data Poisoning Check:** Data poisoning defense was limited to checking if `SECURITY_BREACH` appeared in the error context. A sneaky payload disguised as a simple schema error (e.g., Type Mismatch) would bypass this check and reach the LLM, potentially jailbreaking the repair engine.
3. **Hardcoded Thresholds:** Values like `MAX_REPAIR_ATTEMPTS` (3) and `QUARANTINE_ERROR_THRESHOLD` (5) were statically embedded in the code, requiring a redeployment to change how aggressively the system quarantines or how much token budget it consumes.
4. **Hardcoded Telemetry Levels:** OpenTelemetry logs always defaulted to `SeverityNumber=9` (INFO), making it difficult to filter out noise in production environments.

## Decision
To maximize defensive hardening and operational flexibility, the following changes were made:
1. **Dynamic Fail-Closed Policy:** The MCP fetch operation now respects the `MCP_FAILURE_POLICY` environment variable. If set to `FAIL_CLOSED`, the system will block all traffic when MCP is unreachable, prioritizing security over availability.
2. **Mandatory Pre-Repair Sanitization:** Inside the `decider_node`, before routing any packet to the `repair` node, the raw payload is now mandatorily passed through `SecuritySanitizer.check_payload()`. Any hidden prompt injections will instantly trigger an `end` (Drop) state, regardless of the schema error context.
3. **Environment-Driven Limits:** `MAX_REPAIR_ATTEMPTS` and `QUARANTINE_ERROR_THRESHOLD` are now read dynamically from the `.env` file.
4. **Dynamic Telemetry:** `OpenTelemetryLog` pydantic fields `SeverityText` and `SeverityNumber` were updated to use `default_factory`, reading from the `TELEMETRY_LOG_LEVEL` environment variable.

## Consequences
### Positive
- **Zero-Day Prompt Defense:** Even if a malicious payload successfully disguises itself as a mundane schema error, the mandatory sanitizer check before the LLM prevents the repair engine from being compromised.
- **Strict Security:** In highly sensitive environments (e.g., banking), `FAIL_CLOSED` guarantees that no unvalidated traffic can ever pass through the gateway.
- **Operational Agility:** DevOps teams can adjust quarantine sensitivity, log verbosity, and repair budgets on the fly without touching the codebase.

### Negative
- **Potential Outages:** Activating `FAIL_CLOSED` means any hiccup in the MCP registry will immediately halt all inter-agent communication across the network.
