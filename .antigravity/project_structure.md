# SentinelCell Project Structure

## Overview
SentinelCell is a middleware "Immune System" for Multi-Agent Systems (MAS). This file defines the directory hierarchy for the agentic development environment.

## Directory Tree
```text
.
├── .antigravity/           # Agentic instructions and skill definitions
│   ├── instructions.md     # Core behavior & System Immune rules
│   ├── skills/             # Agentic capabilities (healing, traffic control)
│   └── project_structure.md# This file
├── logs/                   # System runtime & audit logs (JSON/Loguru)
├── registry/               # MCP Server & Schema definitions (Pydantic)
├── src/                    # SentinelCell core implementation
│   ├── listener.py         # Interception logic (Sniffer)
│   ├── validator.py        # Semantic integrity engine
│   ├── healer.py           # LLM-based self-healing module
│   └── dashboard.py        # Rich-based live terminal UI
├── tests/                  # Integrity test suites
├── .env                    # Environment variables (GIT IGNORED)
├── README.md               # Kaggle competition documentation
└── main.py                 # Entry point for the Immune System
