# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Note:** Starting from v0.1.3, this file is automatically maintained by
> [release-please](https://github.com/googleapis/release-please) based on
> [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

<!-- release-please-start -->
<!-- release-please-end -->

---

## [0.1.2] - 2026-07-01 — 🚀 Production-Ready Hardening

### 🔒 Security

- **[CRITICAL]** Eliminated `localStorage` API Key security vulnerability — removed
  `sentinel_api_key` from LocalStorage (XSS attack vector). Now relies exclusively on
  HttpOnly `sentinel_session` cookie + First Message Auth pattern for WebSocket connections.
  ({PR-021})
- **[CRITICAL]** Removed WebSocket API Key from URL parameters — tokens no longer
  transmitted in query strings (eliminated HTTP access log snooping). Implemented
  First Message Auth payload pattern in `useBroadcaster.ts` and `useWebsocket.ts`.
  ({PR-022})

### 🐛 Bug Fixes

- **[CRITICAL]** Standardized `LOG_DIR` environment variable across `orchestrator.py`
  and `fastapi_gateway.py` — fixes Docker volume mismatch that caused DLQ/Audit logs to
  be lost on container restart. Now uses `LOG_DIR=/app/logs` (set in `docker-compose.yml`).
  ({PR-020})
- **[HIGH]** Implemented atomic Redis `SET NX` for idempotency cache to eliminate race
  conditions in `/intercept` endpoint. Clients now receive `409 Conflict` if duplicate
  requests arrive simultaneously, preventing duplicate processing. ({PR-023})
- **[HIGH]** Hardened backend exception handling — removed raw exception messages from
  API responses. Implemented specific error codes (`400` for validation, `504` for
  timeout, `500` for internal) with sanitized messages. Detailed errors logged to
  console only. ({PR-024})
- **[MEDIUM]** Corrected `docker-compose.yml` network configuration — changed
  `sentinel_net` from `external: true` to auto-managed, improving local development
  experience. ({PR-026})

### ✨ Features

- Created `/api/hitl/approval` endpoint for Dashboard-based HITL (Human-in-the-Loop)
  approval workflow. Operators can now control repair workflow via "Approve"/"Reject"
  buttons in the Dashboard. ({PR-025})

---

## [0.1.1] - 2026-06-30

### 🐛 Bug Fixes

- Fixed example scripts lifespan (ensured proper shutdown of `SentinelCell` and MCP
  stdio connections) and added `MockChatModel` fallback to allow offline/credential-less
  execution of all self-healing example simulations. ({DECISION-019})

---

## [0.1.0] - 2026-06-21

### 🐛 Bug Fixes

- Corrected outdated `src.healer` import to `src.skills.repair` in
  `.github/workflows/sentinel_ci.yml` Sandbox verification step following the modular
  refactoring. ({DECISION-018})

### ✨ Features

- Drafted `SECURITY.md` and `CONTRIBUTING.md` and updated `README.md` to fully comply
  with `.antigravity/readme_standards.md`. ({DECISION-017})
- Added `.env.example` as a template for required environment variables and created a
  local `.env` file (ignored by git). ({DECISION-014})
- Created `.antigravity/auto_branching_policy.md` to prevent direct commits to `main`
  and enforce conventional branching (`feature/`, `bugfix/`, `docs/`, `chore/`).
  ({DECISION-013})
- Initialized `pyproject.toml` to serve as the standard Python project configuration,
  detailing metadata, main dependencies, and pytest options. ({DECISION-012})
- Created `requirements.txt` to resolve GitHub Actions `setup-python` cache missing
  file error. ({DECISION-011})
- Implemented GitHub Actions pipeline in `.github/workflows/sentinel_ci.yml`
  (Safety Scan, Unit Tests, Sandbox Integration, Docs Verification). ({DECISION-010})
- Created `github_workflow.md` skill to define the CI/CD pipeline strategy and commit
  enforcement rules. ({DECISION-009})
- Added Table of Contents to `README.md` per updated `.antigravity/readme_standards.md`.
  ({DECISION-007})
- Restructured `README.md` to conform to updated `.antigravity/readme_standards.md`,
  including an SVG logo, Apache License 2.0, and links to Changelog and Contributing
  guidelines. ({DECISION-006})
- Enforced English-only documentation rule globally; translated Turkish `README.md`
  headers to English and updated `.antigravity/readme_standards.md`. ({DECISION-005})
- Drafted comprehensive `README.md` compliant with `.antigravity/readme_standards.md`
  including Mermaid diagrams, problem statement, and setup instructions. ({DECISION-004})
- Integrated MCP Server as the central `SchemaRegistry` and updated
  `SemanticValidator` to fetch contracts dynamically via `mcp_client.py`. ({DECISION-003})
- Implemented `SelfHealingEngine` in `src/healer.py` for LLM-based semantic recovery.
  ({DECISION-002})
- Created `tests/` directory structure and added unit tests for `listener.py` and
  `validator.py`. ({DECISION-001})

### ♻️ Refactoring

- Refactored the documented `src/` directory hierarchy in
  `.antigravity/project_structure.md` to introduce modules for `core`, `agents`, `mcp`,
  `antigravity`, `skills`, and `utils`. ({DECISION-016}, {DECISION-015})
- Moved `logs/` directory to `.antigravity/logs/` and updated policy files to enforce
  this. Removed the chevron icon from `assets/logo.svg`. ({DECISION-008})
