# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

### [0.1.0] - 2026-06-21
- [Added] {DECISION-006}: Restructured `README.md` to conform to updated `.antigravity/readme_standards.md`, including an SVG logo, MIT License, and links to Changelog and Contributing guidelines.
- [Added] {DECISION-005}: Enforced English-only documentation rule globally; translated Turkish `README.md` headers to English and updated `.antigravity/readme_standards.md`.
- [Added] {DECISION-004}: Drafted comprehensive `README.md` compliant with `.antigravity/readme_standards.md` including Mermaid diagrams, problem statement, and setup instructions.
- [Added] {DECISION-003}: Integrated MCP Server as the central `SchemaRegistry` and updated `SemanticValidator` to fetch contracts dynamically via `mcp_client.py`.
- [Added] {DECISION-002}: Implemented `SelfHealingEngine` in `src/healer.py` for LLM-based semantic recovery.
- [Added] {DECISION-001}: Created `tests/` directory structure and added unit tests for `listener.py` and `validator.py`.
