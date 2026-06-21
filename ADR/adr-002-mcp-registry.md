# ADR-002: Model Context Protocol (MCP) for Schema Registry

## Status
**Accepted**

## Context
SentinelCell needs to know the correct JSON schema for the target agent to validate intercepted traffic. Hardcoding schemas inside SentinelCell violates the "Separation of Concerns" principle and requires redeploying the Immune System every time a downstream agent updates its API.

## Decision
We chose the **Model Context Protocol (MCP)** to build a centralized, dynamic `SchemaRegistry`.

## Rationale
1. **Dynamic Resolution**: SentinelCell queries the MCP server in real-time (`get_schema(agent_id)`). If an agent updates its schema, SentinelCell instantly adapts without code changes.
2. **Industry Standard**: MCP is emerging as the definitive protocol for connecting AI agents to external data sources.
3. **Security**: Centralizing contracts prevents spoofing. The Immune System only trusts schemas signed by the MCP Registry.

## Consequences
- **Positive**: Absolute decoupling of the validation engine from the agent schemas. High maintainability.
- **Negative**: Introduces a network hop (latency) to fetch schemas, though this can be mitigated with caching (e.g., Redis).
