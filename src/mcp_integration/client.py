import os
import json
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


import sys


class SchemaRegistryClient:
    """
    Client to fetch agent schemas from the local MCP SchemaRegistry Server via stdio.
    """

    def __init__(self, server_script_path: str, env_override: dict = None):
        env = os.environ.copy()
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(server_script_path))
        )
        env["PYTHONPATH"] = project_root

        if env_override:
            env.update(env_override)

        self.server_parameters = StdioServerParameters(
            command=sys.executable, args=["-m", "src.mcp_integration.registry"], env=env
        )
        self._client_context = None
        self._session = None
        self._lock = None

    async def start(self):
        """Starts the persistent stdio subprocess and initializes the session."""
        import asyncio

        if self._lock is None:
            self._lock = asyncio.Lock()

        async with self._lock:
            if self._session is None:
                self._client_context = stdio_client(self.server_parameters)
                read, write = await self._client_context.__aenter__()
                self._session_context = ClientSession(read, write)
                self._session = await self._session_context.__aenter__()
                await self._session.initialize()

    async def stop(self):
        """Stops the subprocess and closes the session."""
        if self._lock is None:
            return
        async with self._lock:
            if self._session:
                try:
                    await self._session_context.__aexit__(None, None, None)
                except Exception:
                    pass
                try:
                    await self._client_context.__aexit__(None, None, None)
                except Exception:
                    pass
                self._session = None
                self._session_context = None
                self._client_context = None

    @asynccontextmanager
    async def connect(self):
        """Context manager to establish a session with the MCP server."""
        await self.start()
        try:
            yield self._session
        finally:
            pass

    async def fetch_schema(self, agent_id: str) -> dict | None:
        """
        Connects to the MCP server, calls the 'get_agent_schema' tool, and returns the schema dict.
        """
        await self.start()
        result = await self._session.call_tool(
            "get_agent_schema", arguments={"agent_id": agent_id}
        )

        if result.content and len(result.content) > 0:
            schema_str = result.content[0].text
            schema_dict = json.loads(schema_str)
            if not schema_dict:  # == {}
                return None
            return schema_dict
        return None

    async def register_schema(self, agent_id: str, schema_dict: dict) -> bool:
        """
        Connects to the MCP server, calls the 'update_agent_schema' tool, and registers the new schema.
        """
        await self.start()
        try:
            schema_json = json.dumps(schema_dict)
            result = await self._session.call_tool(
                "update_agent_schema",
                arguments={"agent_id": agent_id, "schema_json": schema_json},
            )
            if result.content and len(result.content) > 0:
                response_text = result.content[0].text
                if "successfully" in response_text.lower():
                    return True
        except Exception as e:
            print(f"Error registering schema via MCP: {e}")
        return False
