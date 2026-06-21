# ADR 003: Adaptive Learning, Unlearning, and TTL Memory Purge

## Status
Accepted

## Context
In a Multi-Agent System (MAS), agents may frequently exchange malformed or logically invalid JSON payloads. While the `SelfHealingEngine` utilizes LLMs to infer and correct these payloads dynamically, making a zero-shot LLM request every time the same error occurs is highly inefficient, costly, and prone to repeated hallucinations.

To mitigate this, SentinelCell requires an **Adaptive Learning** mechanism. Furthermore, when the LLM makes an incorrect assumption (a hallucination) that fails downstream validation, there must be a mechanism to prevent the system from memorizing and repeating that mistake (Unlearning). Finally, to prevent the Vector Database from growing boundlessly with old, irrelevant data (Memory Bloat), a TTL (Time-To-Live) strategy is necessary.

## Decision

We decided to implement a multi-phase memory system using our **Database Agnostic `MemoryFactory`** (supporting ChromaDB, PGVector, Pinecone, and In-Memory), tightly integrated into the LangGraph orchestration cycle:

1. **Adaptive Learning (RAG):**
   - Every time a packet is successfully healed, the system saves the `Error Context`, `Malformed Payload`, and the `Fixed Payload` into the active VectorDB collection.
   - On subsequent errors, the engine performs a similarity search. If a past experience matches the current schema and error context, it injects the previous solution directly into the LLM prompt. This radically reduces hallucination rates and repair latencies.

2. **Adaptive Unlearning (Negative Feedback Loop):**
   - Because the RAG memory is saved during the *repair* phase (before the `ValidatorAgent` verifies the fix), there is a risk of permanently saving a hallucinated repair.
   - To counteract this, we track the `last_memory_id` (a UUID document ID) within the LangGraph `AgentState`.
   - If the `ValidatorAgent` rejects the healed packet, the graph routes back to the `repair_node`.
   - The `repair_node` detects the presence of `last_memory_id` and immediately executes a `delete_memory(last_memory_id)` operation on the VectorDB.
   - This ensures that hallucinated schemas are actively **pruned** (forgotten) from the memory bank, creating a true, self-correcting Immune System.

3. **Memory Purge & TTL (Time-To-Live):**
   - To prevent unbounded growth, every stored memory now contains a `timestamp` in its metadata.
   - A global `purge_old_memories(days: int)` interface is implemented across all VectorDB providers.
   - The system exposes a `DELETE /memory/purge?days=X` API endpoint to allow scheduled or manual cleanup of out-of-date hallucinations.

## Consequences

### Positive
- **Cost & Speed Efficiency:** Common errors are solved faster and cheaper via past context injection.
- **Self-Correction:** The system naturally eliminates bad knowledge (Unlearning), ensuring long-term stability without manual database cleanup.
- **Memory Optimization:** The TTL/Purge mechanism ensures the VectorDB remains lean and fast.
- **Model & Database Agnostic:** The memory bank persists and cleans itself regardless of which LLM provider or Vector Database is used.

### Negative
- **State Complexity:** The `AgentState` requires careful tracking of `last_memory_id` across the LangGraph nodes.
- **Database Load:** Frequent inserts and deletes (during Unlearning and Purging) require the underlying Vector Database to efficiently handle write/delete heavy workloads.
