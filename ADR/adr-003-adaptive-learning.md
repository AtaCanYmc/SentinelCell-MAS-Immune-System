# ADR 003: Adaptive Learning and Unlearning (Memory Pruning)

## Status
Accepted

## Context
In a Multi-Agent System (MAS), agents may frequently exchange malformed or logically invalid JSON payloads. While the `SelfHealingEngine` utilizes LLMs to infer and correct these payloads dynamically, making a zero-shot LLM request every time the same error occurs is highly inefficient, costly, and prone to repeated hallucinations.

To mitigate this, SentinelCell requires an **Adaptive Learning** mechanism. Furthermore, when the LLM makes an incorrect assumption (a hallucination) that fails downstream validation, there must be a mechanism to prevent the system from memorizing and repeating that mistake.

## Decision

We decided to implement a dual-phase memory system using **ChromaDB** as our Vector Database, heavily integrated into the LangGraph orchestration cycle:

1. **Adaptive Learning (RAG):**
   - Every time a packet is successfully healed, the system saves the `Error Context`, `Malformed Payload`, and the `Fixed Payload` into a ChromaDB collection (`healing_memory`).
   - On subsequent errors, the engine performs a similarity search. If a past experience matches the current schema and error context, it injects the previous solution directly into the LLM prompt. This radically reduces hallucination rates and repair latencies.

2. **Adaptive Unlearning (Negative Feedback Loop):**
   - Because the RAG memory is saved during the *repair* phase (before the `ValidatorAgent` verifies the fix), there is a risk of permanently saving a hallucinated repair.
   - To counteract this, we track the `last_memory_id` (a UUID document ID) within the LangGraph `AgentState`.
   - If the `ValidatorAgent` rejects the healed packet, the graph routes back to the `repair_node`.
   - The `repair_node` detects the presence of `last_memory_id` and immediately executes a `collection.delete(ids=[last_memory_id])` operation.
   - This ensures that hallucinated schemas are actively **pruned** (forgotten) from the memory bank, creating a true, self-correcting Immune System.

## Consequences

### Positive
- **Cost & Speed Efficiency:** Common errors are solved faster and cheaper via past context injection.
- **Self-Correction:** The system naturally eliminates bad knowledge, ensuring long-term stability without manual database cleanup.
- **Model Agnostic Memory:** The memory bank persists regardless of which LLM provider (OpenAI, DeepSeek, Gemini, etc.) generated the fix.

### Negative
- **State Complexity:** The `AgentState` requires careful tracking of `last_memory_id` across the LangGraph nodes.
- **ChromaDB Dependency:** The adaptive features tightly couple the healing performance to the availability of the local ChromaDB instance. If ChromaDB is unavailable, the system defaults back to zero-shot healing.
