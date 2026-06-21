# SentinelCell: Auto-Commit Policy

## Overview
SentinelCell agents have the authority to commit validated code repairs directly to the repository. This policy defines the "Guardrails" for autonomous commits.

## Commit Criteria
1. **Validation Success:** A commit is ONLY triggered if `validation_skill` reports a schema match AND `antigravity_skill` (sandbox) returns `Exit Code 0`.
2. **Context Requirement:** Every commit MUST reference a `Decision ID` from `logs/agent_decisions.json`.
3. **Safety Buffer:** No more than 3 consecutive commits are allowed without human review.

## Commit Message Format
The agent must use the following standard:
`[SentinelCell-AutoFix] {DecisionID}: {Brief Description of the repair}`

## Security Measures
- **Author Identity:** Commits are signed with the SentinelCell Agent identity key.
- **Forbidden Operations:** Agents are strictly forbidden from committing changes to:
  - `main.py` (Orchestration logic)
  - `.env` (Sensitive configuration)
  - `skills/` (Core logic templates)

## Verification
- Before pushing, the agent must run the local test suite (`pytest tests/`) in the Antigravity sandbox. If any test fails, the commit is aborted.
