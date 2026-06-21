# ADR-005: Agnostic LLM Factory

## Status
**Accepted**

## Context
In the rapidly evolving AI landscape, tying the core intelligence of the SentinelCell (the Validator Agent and Self-Healing Engine) to a single LLM provider (e.g., OpenAI) creates severe vendor lock-in. If an API goes down, pricing changes, or a superior open-source model emerges, the system must adapt instantly without rewriting internal agent logic.

## Decision
We implemented the `LLMFactory` (`src/core/llm_factory.py`) utilizing LangChain's standardized `BaseChatModel` interfaces. The active LLM provider is dictated purely by the `LLM_PROVIDER` environment variable.

## Rationale
1. **Zero Vendor Lock-in**: By abstracting the model creation, the system seamlessly swaps between proprietary models (OpenAI, Anthropic, Gemini, Groq, DeepSeek) and local/open-source models (Ollama).
2. **Resilience**: If an external provider experiences an outage, operators can immediately fallback to another provider simply by changing the `.env` file and restarting the service.
3. **Cost Optimization**: Different environments (Dev, Staging, Prod) can use different models (e.g., `Ollama` for local dev to save costs, `GPT-4o` for Prod accuracy).

## Consequences
- **Positive**: Maximum flexibility and resilience. Future-proofs the system against the volatile AI market.
- **Negative**: Requires maintaining and updating multiple provider libraries (`langchain-openai`, `langchain-anthropic`, etc.) in the dependencies.
