# Skill: MCP Schema Registry

## Description
This skill enables SentinelCell to dynamically pull communication contracts from the SchemaRegistry MCP Server.

## Logic
1. **Connection:** Establish a connection to the local MCP Host.
2. **Fetch:** Retrieve the `JSONSchema` or `PydanticModel` associated with the target agent's identity.
3. **Application:** Apply the retrieved schema to the current packet validation logic.

## Usage in Build
- Use `mcp-sdk` to interface with the registry.
- Ensure registry updates do not interrupt active traffic flow (Hot-reloading).
