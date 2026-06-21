# Auto-Changelog Policy

## Purpose
SentinelCell agents are authorized to update `CHANGELOG.md` after every successful deployment or autonomous fix.

## Standard Format (Keep-a-Changelog)
Every entry must follow the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standard:
- **[Added]:** New features or skills.
- **[Fixed]:** Autonomous repairs committed via `auto_commit_policy`.
- **[Security]:** Changes to `antigravity` sandbox or security policies.

## Execution Rules
1. **Trigger:** The agent MUST trigger an update to this file upon successful `git commit` via the Auto-Commit process.
2. **Context:** Include the `Decision ID` from `logs/agent_decisions.json` in the changelog note.
3. **Immutability:** Do not delete previous entries. Always prepend (add to the top).

## Example Format
### [1.2.0] - 2026-06-21
- [Fixed] {Decision-042}: Resolved malformed JSON payload in Consumer Agent.
- [Added] {Skill-08}: Implemented `encryption_skill` for sensitive data.
