# Contributing to SentinelCell

We welcome contributions to the SentinelCell MAS Immune System! To maintain the structural integrity and security of the Multi-Agent environment, please follow these guidelines carefully.

## 1. Local Development Setup

To run the project locally on bare-metal (without Docker) for development:

```bash
# 1. Clone the repo
git clone https://github.com/your-org/SentinelCell-MAS-Immune-System.git
cd SentinelCell-MAS-Immune-System

# 2. Setup Virtual Environment
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Install Requirements (including dev tools)
pip install -r requirements.txt
pip install pytest flake8 black

# 4. Configure Environment
cp .env.example .env
# Edit .env with your LLM keys
```

## 2. Linting & Formatting

We use `black` for code formatting and `flake8` for linting. Please ensure your code passes both before submitting a Pull Request.

```bash
black src/ examples/
flake8 src/ examples/
```

## 3. Testing

We use `pytest` for unit testing. Make sure all tests pass:

```bash
pytest tests/
```

## 4. Branching Strategy
All development must occur on dedicated feature branches.
Please prefix your branches correctly:
- `feature/...` for new capabilities
- `bugfix/...` for bug fixes
- `docs/...` for documentation updates
- `chore/...` for routine maintenance

## 5. Pull Request & Merge Rules
1. Open a PR and ensure the `Sentinel-Verified` CI actions (pytest & sandbox validation) succeed.
2. Ensure your code passes all linting (`black`, `flake8`) and unit tests.
3. A human reviewer must approve the PR with an "LGTM".
4. Only after approval, the PR can be merged to `main`.

## 6. Code & Documentation
- **Architecture**: The core orchestrator uses **LangGraph**. Ensure any new nodes return a valid `AgentState`.
- **Language**: All documentation and code comments must be exclusively in **English**.
- **Aesthetic**: CLI output should utilize the `rich` library and maintain high observability standards.

Thank you for helping us make Multi-Agent Systems robust and resilient!
