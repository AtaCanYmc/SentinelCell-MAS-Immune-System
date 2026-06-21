# Security Policy

## Supported Versions

Currently, SentinelCell is in rapid development (version `0.1.0`). We provide security updates for the `main` branch.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.0   | :white_check_mark: |

## Safe Execution Environment (Sandbox)
SentinelCell utilizes the Antigravity Sandbox to test all intercepted JSON payloads, execute unit tests, and evaluate self-healing code. This execution boundary ensures that even if an Agent hallucinates malicious code, the underlying host system remains protected.

## API Key Protection
The Self-Healing Engine interfaces with external LLM providers via LangChain (e.g., OpenAI, Anthropic, or Local Ollama).
**Never commit your `.env` file to version control.**
We have included a `.env.example` file and configured `.gitignore` to prevent accidental exposure of your `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. If a key is accidentally committed, revoke it immediately via your provider's dashboard. For maximum privacy, configure the orchestrator to fallback exclusively to `LOCAL_OLLAMA`.

## Reporting a Vulnerability

If you discover a security vulnerability within SentinelCell, please **do not** open a public issue. Instead, contact the core maintainers directly.
Please include:
- A description of the vulnerability.
- Steps to reproduce the issue.
- Potential impact on the "Immune System" middleware.

We aim to acknowledge all reports within 48 hours and release an emergency `hotfix/` branch in accordance with our PR Merge Policy.
