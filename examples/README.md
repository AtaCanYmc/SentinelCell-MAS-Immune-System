# SentinelCell Examples

This directory contains live demonstrations to help you understand the capabilities of the **SentinelCell MAS Immune System** architecture hands-on.

You can run the example scripts below directly from the terminal. Before running them, ensure you are in the project root directory and your `.env` file is properly configured with the respective LLM API keys. Do not forget to prefix your commands with `PYTHONPATH=.` to set the necessary Python path.

## Examples

### 1. Basic Usage (`basic_usage.py`)
This is the most fundamental "Hello World" style usage scenario. An intentionally malformed JSON payload (missing the required 'message' field) is created and passed to the LangGraph-based `SentinelCell`. It demonstrates how the agent rejects the payload (validation) and subsequently corrects it using the Self-Healing mechanism.
```bash
PYTHONPATH=. python examples/basic_usage.py
```

### 2. Multi-Agent Flow (`multi_agent_flow.py`)
Demonstrates how SentinelCell acts as an intermediary layer (middleware/immune system) within a classic Producer-Consumer model.
The Producer emits faulty data; the Consumer strictly accepts clean data. SentinelCell intercepts the traffic, heals the payload, and delivers the clean data to the Consumer.
```bash
PYTHONPATH=. python examples/multi_agent_flow.py
```

### 3. Custom Skill Demo (`custom_skill_demo.py`)
Shows how to build and integrate a custom "Skill" node on top of SentinelCell. In this example, a `Sanitizer` node is constructed and added to the LangGraph state machine. It detects sensitive payloads containing a password and masks the password as "******".
```bash
PYTHONPATH=. python examples/custom_skill_demo.py
```
