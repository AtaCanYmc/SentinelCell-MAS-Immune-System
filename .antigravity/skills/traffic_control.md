# Skill: Traffic Controller (Middleware)

## Purpose
Manage the flow of communication between agents without introducing latency or bottlenecks.

## Implementation Rules
- **Non-Intrusive:** The interception must be near-instant. Use asynchronous listeners.
- **Reporting:** Keep the `rich` dashboard updated in real-time.
- **Contract Enforcement:** If an agent deviates from the defined API contract (SchemaRegistry), treat it as a "semantic breach" and trigger the Healing Protocol immediately.
