import os
import json
import redis.asyncio as redis
from mcp.server.fastmcp import FastMCP
from registry.base_contracts import StatusContract

mcp = FastMCP("SchemaRegistry")


def get_redis_client():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis.from_url(redis_url)


@mcp.tool()
async def get_agent_schema(agent_id: str) -> str:
    """
    Retrieve the JSON Schema for a specific agent's communication contract from Redis.
    """
    client = get_redis_client()
    try:
        schema = await client.get(f"schema:{agent_id}")
        if schema:
            return schema.decode("utf-8")

        # Fallback to local default if not in Redis
        if agent_id == "Agent_Beta":
            default_schema = json.dumps(StatusContract.model_json_schema())
            # Auto-seed the database
            await client.set(f"schema:{agent_id}", default_schema)
            return default_schema

        return "{}"  # Empty JSON means no strict schema enforced
    finally:
        await client.aclose()


@mcp.tool()
async def update_agent_schema(agent_id: str, schema_json: str) -> str:
    """
    Dynamically register or update an agent's JSON Schema in the Registry.
    """
    client = get_redis_client()
    try:
        # Validate that the provided string is valid JSON
        json.loads(schema_json)
        await client.set(f"schema:{agent_id}", schema_json)
        return f"Schema for {agent_id} updated successfully in Redis Registry."
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided."
    finally:
        await client.aclose()


if __name__ == "__main__":
    # Start the FastMCP server with stdio transport
    mcp.run(transport="stdio")
