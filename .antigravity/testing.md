# SentinelCell: Testing Strategy

SentinelCell adopts a **Test-Driven Agentic Engineering** approach. We ensure that every self-healing action and validation check is verifiable and reproducible.

## 1. Unit Testing
Each skill is tested in isolation to ensure logic accuracy.
- **Framework:** `pytest`
- **Scope:** Validation logic, Pydantic schema mapping, and repair prompt generation.
- **Location:** `tests/unit/`

## 2. Sandbox Verification (Antigravity Integration)
Since SentinelCell relies on the Antigravity CLI for safe execution, we must verify that the sandbox environment is enforcing constraints correctly.
- **Test:** Verify that the `RepairSkill` cannot execute unauthorized shell commands.
- **Success Criteria:** Sandbox should return `Exit Code 1` (Restricted) for unauthorized attempts and `Exit Code 0` for safe repair logic.
- **Location:** `tests/sandbox/test_sandbox_security.py`

## 3. Integration Testing (Agentic Loop)
Testing the "Immune System" flow: `Producer -> SchemaGuard -> Consumer`.
- **Scenario:** Inject a malformed JSON payload and verify that `SentinelCell` detects, repairs, and forwards the payload within the defined latency limit (<500ms).
- **Location:** `tests/integration/test_traffic_flow.py`

## 4. How to Run
```bash
# Run the complete test suite
pytest tests/ --cov=./schema_guard

# Run security-focused sandbox tests
pytest tests/sandbox/ --sandbox-mode=strict
