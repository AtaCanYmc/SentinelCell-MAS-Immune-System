# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

### [0.1.2] - 2026-07-01 🚀 **PRODUCTION-READY HARDENING**
- [**FIXED - CRITICAL**] {PR-020}: Standardized LOG_DIR environment variable across `orchestrator.py` and `fastapi_gateway.py` - fixes Docker volume mismatch that caused DLQ/Audit logs to be lost on container restart. Now uses `LOG_DIR=/app/logs` (set in docker-compose.yml).
- [**FIXED - CRITICAL**] {PR-021}: Eliminated localStorage API Key security vulnerability - removed `sentinel_api_key` from LocalStorage (XSS attack vector). Now relies exclusively on HttpOnly `sentinel_session` cookie + First Message Auth pattern for WebSocket connections.
- [**FIXED - CRITICAL**] {PR-022}: Removed WebSocket API Key from URL parameters - tokens no longer transmitted in query strings (eliminated HTTP access log snooping). Implemented First Message Auth payload pattern in `useBroadcaster.ts` and `useWebsocket.ts`.
- [**FIXED - HIGH**] {PR-023}: Implemented atomic Redis SET NX for idempotency cache to eliminate race conditions in `/intercept` endpoint. Clients now receive 409 Conflict if duplicate requests arrive simultaneously, preventing duplicate processing.
- [**FIXED - HIGH**] {PR-024}: Hardened backend exception handling - removed raw exception messages from API responses. Implemented specific error codes (400 for validation, 504 for timeout, 500 for internal) with sanitized messages. Detailed errors logged to console only.
- [**ADDED**] {PR-025}: Created `/api/hitl/approval` endpoint for Dashboard-based HITL (Human-in-the-Loop) approval workflow. Operatörer artık Dashboard'dan "Approve"/"Reject" butonlarına basarak repair workflow'unu kontrol edebiliyor.
- [**FIXED - MEDIUM**] {PR-026}: Corrected docker-compose.yml network configuration - changed `sentinel_net` from `external: true` to auto-managed, improving local development experience.

### [0.1.1] - 2026-06-30
- [Fixed] {DECISION-019}: Fixed example scripts lifespan (ensured proper shutdown of `SentinelCell` and MCP stdio connections) and added `MockChatModel` fallback to allow offline/credential-less execution of all self-healing example simulations.

### [0.1.0] - 2026-06-21
- [Fixed] {DECISION-018}: Corrected outdated `src.healer` import to `src.skills.repair` in `.github/workflows/sentinel_ci.yml` Sandbox verification step following the modular refactoring.
- [Added] {DECISION-017}: Drafted `SECURITY.md` and `CONTRIBUTING.md` and updated `README.md` to fully comply with `.antigravity/readme_standards.md`.
- [Changed] {DECISION-016}: Refactored the documented `src/` directory hierarchy in `.antigravity/project_structure.md` to introduce modules for `core`, `agents`, `mcp`, `antigravity`, `skills`, and `utils`.
- [Changed] {DECISION-015}: Refactored the documented `src/` directory hierarchy in `.antigravity/project_structure.md` to introduce modules for `core`, `agents`, `mcp`, `antigravity`, `skills`, and `utils`.
- [Added] {DECISION-014}: Added `.env.example` as a template for required environment variables and created a local `.env` file (ignored by git).
- [Added] {DECISION-013}: Created `.antigravity/auto_branching_policy.md` to prevent direct commits to `main` and enforce conventional branching (`feature/`, `bugfix/`, `docs/`, `chore/`).
- [Added] {DECISION-012}: Initialized `pyproject.toml` to serve as the standard Python project configuration, detailing metadata, main dependencies, and pytest options.
- [Fixed] {DECISION-011}: Created `requirements.txt` to resolve GitHub Actions `setup-python` cache missing file error.
- [Added] {DECISION-010}: Created `.github/workflows/sentinel_ci.yml` implementing the GitHub Actions pipeline (Safety Scan, Unit Tests, Sandbox Integration, Docs Verification).
- [Added] {DECISION-009}: Created `github_workflow.md` skill to define the CI/CD pipeline strategy and commit enforcement rules.
- [Changed] {DECISION-008}: Moved `logs/` directory to `.antigravity/logs/` and updated policy files to enforce this. Removed the chevron icon from `assets/logo.svg`.
- [Added] {DECISION-007}: Added Table of Contents to `README.md` per updated `.antigravity/readme_standards.md`.
- [Added] {DECISION-006}: Restructured `README.md` to conform to updated `.antigravity/readme_standards.md`, including an SVG logo, Apache License 2.0, and links to Changelog and Contributing guidelines.
- [Added] {DECISION-005}: Enforced English-only documentation rule globally; translated Turkish `README.md` headers to English and updated `.antigravity/readme_standards.md`.
- [Added] {DECISION-004}: Drafted comprehensive `README.md` compliant with `.antigravity/readme_standards.md` including Mermaid diagrams, problem statement, and setup instructions.
- [Added] {DECISION-003}: Integrated MCP Server as the central `SchemaRegistry` and updated `SemanticValidator` to fetch contracts dynamically via `mcp_client.py`.
- [Added] {DECISION-002}: Implemented `SelfHealingEngine` in `src/healer.py` for LLM-based semantic recovery.
- [Added] {DECISION-001}: Created `tests/` directory structure and added unit tests for `listener.py` and `validator.py`.
