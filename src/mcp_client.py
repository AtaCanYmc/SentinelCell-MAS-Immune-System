import os
import json
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class SchemaRegistryClient:
    """
    Client to fetch agent schemas from the local MCP SchemaRegistry Server via stdio.
    """

    def __init__(self, server_script_path: str):
        env = os.environ.copy()
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(server_script_path))
        )
        env["PYTHONPATH"] = project_root

        self.server_parameters = StdioServerParameters(
            command="python", args=[server_script_path], env=env
        )

    @asynccontextmanager
    async def connect(self):
        """Context manager to establish a session with the MCP server."""
        async with stdio_client(self.server_parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async def fetch_schema(self, agent_id: str) -> dict | None:
        """
        Connects to the MCP server, calls the 'get_agent_schema' tool, and returns the schema dict.
        """
        async with self.connect() as session:
            result = await session.call_tool(
                "get_agent_schema", arguments={"agent_id": agent_id}
            )

            if result.content and len(result.content) > 0:
                schema_str = result.content[0].text
                schema_dict = json.loads(schema_str)
                if not schema_dict:  # == {}
                    return None
                return schema_dict
            return None
