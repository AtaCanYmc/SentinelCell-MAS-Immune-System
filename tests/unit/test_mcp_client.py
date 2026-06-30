import pytest
from src.mcp_integration.client import SchemaRegistryClient
from unittest.mock import patch, MagicMock


def test_mcp_client_init():
    client = SchemaRegistryClient("dummy_path", {"TEST_ENV": "val"})
    assert client.server_parameters.env.get("TEST_ENV") == "val"


@pytest.mark.asyncio
async def test_mcp_client_fetch():
    with (
        patch("src.mcp_integration.client.stdio_client") as mock_stdio,
        patch("src.mcp_integration.client.ClientSession") as mock_session,
    ):
        mock_read = MagicMock()
        mock_write = MagicMock()

        mock_stdio_context = MagicMock()
        mock_stdio_context.__aenter__.return_value = (mock_read, mock_write)
        mock_stdio_context.__aexit__.return_value = None
        mock_stdio.return_value = mock_stdio_context

        session_instance = MagicMock()
        session_instance.initialize = (
            MagicMock()
        )  # Should be AsyncMock but since we just mock the return it's fine

        mock_session_context = MagicMock()
        mock_session_context.__aenter__.return_value = session_instance
        mock_session_context.__aexit__.return_value = None
        mock_session.return_value = mock_session_context

        client = SchemaRegistryClient("dummy_path")

        # Test fetch
        async def mock_call_tool(*args, **kwargs):
            return MagicMock(content=[MagicMock(text='{"type": "object"}')])

        session_instance.call_tool = mock_call_tool

        async def mock_initialize(*args, **kwargs):
            return None

        session_instance.initialize = mock_initialize

        result = await client.fetch_schema("AgentA")
        assert result.get("type") == "object"
