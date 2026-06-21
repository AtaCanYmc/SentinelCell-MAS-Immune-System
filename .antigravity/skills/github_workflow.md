# GitHub Workflow Strategy

SentinelCell uses GitHub Actions to enforce the "Immune System" standards. Every PR (Pull Request) or push is treated as a potential "infection" that must be validated.

## Workflow Phases
1. **Safety Scan:** `Antigravity CLI` scans the codebase for hardcoded secrets or unauthorized system calls.
2. **Unit Testing:** `pytest` executes all unit tests defined in `tests/unit/`.
3. **Sandbox Integration:** The code is deployed to a temporary Antigravity sandbox environment to verify the "Repair Logic".
4. **Docs Verification:** A script checks if `CHANGELOG.md` and `README.md` follow the predefined standards.

## Commit Enforcement
- A commit is rejected if `pytest` or `Antigravity Sandbox` returns a non-zero exit code.
- This ensures that only "Sentinel-Verified" code enters the production branch.
