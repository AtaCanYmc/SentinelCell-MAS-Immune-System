# Auto-Branching Policy

To maintain a clean, protected, and CI-friendly `main` branch, all agentic developments MUST be performed on a dedicated branch. Direct commits to `main` are **strictly forbidden** unless explicitly authorized by the user for an emergency hotfix.

## Branch Naming Conventions
When starting a new task, the agent must create a new branch based on the nature of the development using the following prefixes:

- **`feature/...`**: For new features, logic additions, or architectural changes.
  - *Example:* `feature/mcp-integration`
- **`bugfix/...`**: For fixing failing tests, syntax errors, or logic bugs.
  - *Example:* `bugfix/healer-validation`
- **`docs/...`**: For updates to README, standard guidelines, or comments.
  - *Example:* `docs/readme-update`
- **`chore/...`**: For maintenance tasks, dependency updates, CI/CD workflows, or configuration files (`.gitignore`, `pyproject.toml`).
  - *Example:* `chore/pyproject-setup`

## Workflow Enforcement
1. **Branch Creation:** Before making any source code modifications or executing tool calls that alter files, the agent MUST run `git checkout -b <branch_name>`.
2. **Implementation:** Write code, run unit tests via `pytest`, and ensure `pre-commit` passes.
3. **Commit:** Commit the changes to the active branch referencing the decision ID (as per `.antigravity/auto_commit_policy.md`).
4. **Pull Request / Merge:** The agent MUST NOT merge directly to `main`. After committing, the agent should inform the user that the branch is ready for review and integration.
