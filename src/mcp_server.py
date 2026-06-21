import json
from mcp.server.fastmcp import FastMCP
from registry.base_contracts import StatusContract

mcp = FastMCP("SchemaRegistry")

# Dynamic mapping of agent IDs to their respective contracts
# In a real system, this could come from a database.
_REGISTRY = {"Agent_Beta": StatusContract.model_json_schema()}


@mcp.tool()
def get_agent_schema(agent_id: str) -> str:
    """
    Retrieve the JSON Schema for a specific agent's communication contract.
    """
    schema = _REGISTRY.get(agent_id)
    if schema:
        return json.dumps(schema)
    return "{}"  # Empty JSON means no strict schema enforced


if __name__ == "__main__":
    # Start the FastMCP server with stdio transport
    mcp.run(transport="stdio")
