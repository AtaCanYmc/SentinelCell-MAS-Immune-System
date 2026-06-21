# SentinelCell: Auto-PR & Merge Policy

## Overview
This policy defines the rules for automated Pull Requests (PR) and merging procedures. SentinelCell agents are empowered to propose changes, but the integration into the `main` branch follows a "Human-in-the-Loop" (HITL) gatekeeping model.

### Branching
Read `.antigravity/auto_branching_policy.md` file to generate branch.

## 1. Automated PR Creation
- **Trigger:** Once a branch (feature, bugfix, or chore) has passed all local `pytest` and `Antigravity` sandbox verifications.
- **PR Content:** The agent MUST generate a PR body containing:
    - **Summary:** Link to the relevant `Decision ID` in `logs/agent_decisions.json`.
    - **Impact:** Which files were modified and why.
    - **Verification Results:** A summary of the sandbox exit codes and test coverage metrics.
    - **Labels:** Automatically assign labels based on the branch prefix (e.g., `status/needs-review`, `type/fix`, `type/feat`).

## 2. Merge Constraints
- **Strict Prohibition:** Agents are **forbidden** from merging their own PRs into the `main` branch.
- **Human Approval:** PRs require a manual "LGTM" (Looks Good To Me) or approval from the human collaborator.
- **Automated Validation Gate:** A merge is only possible if the GitHub Action (`sentinel_ci.yml`) status is `SUCCESS`.

## 3. Merge Procedure
1. **Request:** The agent creates the PR and notifies the user via the `log` or CLI.
2. **Review:** Human collaborator reviews the changes.
3. **Execution:** Upon approval, the agent executes `git checkout main && git merge <branch_name>`.
4. **Cleanup:** After a successful merge, the agent MUST delete the source branch and archive the `Decision ID` as `COMPLETED` in the logs.

## 4. Emergency Override
- If a critical bug is detected in `main`, the user may authorize an "Emergency Hotfix" (branch `hotfix/...`), which allows bypassing the manual review gate, provided that the `Antigravity` sandbox validation still passes.
