# ADR-001: Selection of LangGraph for Agentic Orchestration

## Status
**Accepted**

## Context
Multi-Agent Systems (MAS) inherently produce non-deterministic execution paths. When SentinelCell intercepts a payload, the validation might pass, fail, or require multiple recursive attempts (retries) to heal the semantic structure. A linear scripting approach (e.g., standard LangChain Chains) is too rigid for complex fallback loops (OpenAI -> Anthropic -> Local).

## Decision
We elected to use **LangGraph** to model SentinelCell's internal logic as a State Machine (StateGraph).

## Rationale
1. **Cyclic Execution**: LangGraph natively supports cycles, allowing us to loop the `repair_node` until `max_attempts` is exhausted.
2. **State Persistence**: The `AgentState` `TypedDict` maintains the context (`schema_dict`, `payload`, `repair_attempts`) immutably across node transitions.
3. **Resilience**: It makes the dynamic fallback architecture (LLMFactory) trivial to implement by routing through different LLM providers on each cycle iteration.

## Consequences
- **Positive**: Extremely robust, crash-proof pipeline. The orchestration logic is highly observable.
- **Negative**: Adds a slight learning curve and dependency overhead compared to raw async functions.
