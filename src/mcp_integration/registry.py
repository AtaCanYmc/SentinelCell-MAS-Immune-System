import json
from mcp.server.fastmcp import FastMCP
from registry.base_contracts import StatusContract
from src.core.registry_factory import registry_store

mcp = FastMCP("SchemaRegistry")


@mcp.tool()
async def get_agent_schema(agent_id: str) -> str:
    """
    Retrieve the JSON Schema for a specific agent's communication contract from the Agnostic Registry.
    """
    try:
        schema = await registry_store.get_schema(agent_id)
        if schema:
            return schema

        # Fallback to local default if not in Registry
        if agent_id == "Agent_Beta":
            default_schema = json.dumps(StatusContract.model_json_schema())
            # Auto-seed the database
            await registry_store.update_schema(agent_id, default_schema)
            return default_schema

        return "{}"  # Empty JSON means no strict schema enforced
    except Exception as e:
        print(f"Schema Fetch Error: {e}")
        return "{}"


@mcp.tool()
async def update_agent_schema(agent_id: str, schema_json: str) -> str:
    """
    Dynamically register or update an agent's JSON Schema in the Agnostic Registry.
    """
    try:
        # Validate that the provided string is valid JSON
        json.loads(schema_json)
        await registry_store.update_schema(agent_id, schema_json)
        return f"Schema for {agent_id} updated successfully in Agnostic Registry."
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided."
    except Exception as e:
        return f"Error updating registry: {str(e)}"


if __name__ == "__main__":
    # Start the FastMCP server with stdio transport
    mcp.run(transport="stdio")
