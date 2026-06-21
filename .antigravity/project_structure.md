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
├── src/                    # SentinelCell core implementation
│   ├── __init__.py
│   ├── main.py                 # The Orchestrator (Entry point for the Multi-Agent System)
│   ├── core/
│   │   ├── orchestrator.py     # Manages the Agentic Loop and workflow DAGs
│   │   └── logger.py           # Handles logging for agent_decisions.json
│   ├── agents/
│   │   ├── producer.py         # Producer agent (Data Source)
│   │   ├── consumer.py         # Consumer agent (Data Receiver)
│   │   └── validator_agent.py  # The SentinelCell (The "Immune System" agent)
│   ├── mcp_integration/
│   │   ├── registry.py         # MCP server managing schema definitions
│   │   └── client.py           # Client implementation for inter-agent communication
│   ├── antigravity/
│   │   ├── sandbox.py          # Wrapper for Antigravity CLI (Execution isolation)
│   │   └── integrity.py        # Logic to verify sandbox-executed code/data
│   ├── skills/
│   │   ├── base.py             # Abstract BaseSkill interface
│   │   ├── validation.py       # Implementation of validation logic
│   │   └── repair.py           # Implementation of self-healing logic
│   └── utils/
│       └── schema_tools.py     # Pydantic models and helper functions
├── tests/                  # Integrity test suites
├── .env                    # Environment variables (GIT IGNORED)
├── README.md               # Kaggle competition documentation
