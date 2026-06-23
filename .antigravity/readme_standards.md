# SentinelCell README Standards (v2.0)

To maintain enterprise-grade consistency, readability, and open-source excellence across our agentic ecosystem, every component of SentinelCell must strictly follow these documentation guidelines.

## 1. The Anatomy of a SentinelCell README

Every README must be structured in the following order to ensure a logical flow for the reader:

1. **Brand Identity (Logo & Title):** Center-aligned project logo followed by the `<h1>` Project Name.
2. **Dynamic Badges:** Include dynamically fetched badges (via shields.io) for: Version, Build Status, Python/Node versions, License, and the Kaggle Capstone tag. *Do not use hardcoded version badges.*
3. **Background & Acknowledgments:** A brief section detailing the project's origins (e.g., "Built for the Kaggle AI Agents: Intensive Vibe Coding Capstone") and crediting third-party libraries or contributors. *Never hide this in the footer.*
4. **Table of Contents:** Auto-generated navigational links.
5. **Problem Statement & Philosophy:** Max 300 words explaining the "pain point" and the "vibe/intent" behind the solution.
6. **Agentic & Full-Stack Architecture:** A visual representation (Mermaid/SVG) of the flow. **Rule:** The diagram *must* include both the agentic logic (LangGraph/MCP) and the Observability/UI layers (React/Vite).
7. **Prerequisites & Quick Start:**
* Must include distinct steps for both **Backend** (Docker, Python `pip install -e .[dev]`) and **Frontend** (`npm install`, `npm run dev`) developer setups.
8. **Configuration (.env Example):** A mandatory markdown code block providing minimal, non-sensitive environment variables required to boot the system.
9. **Visual Proof & Examples:** Terminal outputs, UI screenshots, or simulation commands demonstrating the tool in action.
10. **Sandbox & Security Policies:**
* Reference the `.antigravity/auto_changelog_policy.md` for agentic permissions.
* **Security Disclaimer:** Mandatory warning regarding external LLM API interactions and Data Poisoning risks.
11. **Project References:** Link to `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, and the `LICENSE` file.

## 2. Style & Tone Guidelines

* **Global Language:** Use ONLY **English** for all documentation, code comments, and diagrams to maintain global open-source accessibility.
* **Tone:** Professional, authoritative, yet approachable. Avoid unexplained jargon. Use active voice and imperative mood for instructions (e.g., "Run this command" instead of "You should run this command").
* **Code-First Explanation:** Use markdown code blocks for every configuration, shell command, or JSON payload example.
* **Conciseness:** Keep technical descriptions under 300 words per section. Emphasize readability.

## 3. Mandatory Section Matrix

If a README is missing any of the below, it fails the CI/CD documentation check.

| Section | Purpose |
| --- | --- |
| **Philosophy** | The architectural intent and core defense logic (The "Immune System" vibe). |
| **Capability Matrix** | List of specific skills/tools the agent is authorized to use. |
| **Deployment / DX** | Setup Wizard (`setup.sh`), Local Dev, and Docker guidelines. |
| **Architecture Diagram** | Clear mapping of data ingestion, validation, LLM routing, and UI state. |

## 4. Maintenance & Versioning Rules

* **Auto-Update Trigger:** If a new skill is added or a core architecture decision changes, the agent MUST trigger a README update via the `auto-commit` workflow.
* **Versioning:** Strictly follow Semantic Versioning (MAJOR.MINOR.PATCH). Ensure the GitHub release tags match the documentation versions.
