# Contributing to SentinelCell

We welcome contributions to the SentinelCell MAS Immune System! To maintain the structural integrity and security of the Multi-Agent environment, please follow these guidelines carefully.

## 1. Branching Strategy
Direct commits to the `main` branch are strictly forbidden. All development must occur on dedicated feature branches.
Please prefix your branches correctly:
- `feature/...` for new capabilities
- `bugfix/...` for bug fixes
- `docs/...` for documentation updates
- `chore/...` for routine maintenance

For detailed rules, see [.antigravity/auto_branching_policy.md](.antigravity/auto_branching_policy.md).

## 2. Pull Request & Merge Rules
We enforce a "Human-in-the-Loop" gatekeeping mechanism. AI Agents cannot merge their own code.
1. Open a PR and ensure the `Sentinel-Verified` CI actions (pytest & sandbox validation) succeed.
2. A human reviewer must approve the PR with an "LGTM".
3. Only after approval, the PR can be merged to `main`.
4. Please link to the corresponding `Decision ID` from `logs/agent_decisions.json`.

For detailed rules, see [.antigravity/auto_pr_merge_policy.md](.antigravity/auto_pr_merge_policy.md).

## 3. Code & Documentation
- **Architecture**: The core orchestrator uses **LangGraph**. Ensure any new nodes return a valid `AgentState`.
- **Language**: All documentation and code comments must be exclusively in **English**.
- **Tests**: Ensure that any new components are covered by unit tests in `tests/` using Pytest.
- **Aesthetic**: CLI output should utilize the `rich` library and maintain our "Hackerman" theme colors.

Thank you for helping us make Multi-Agent Systems robust and resilient!
