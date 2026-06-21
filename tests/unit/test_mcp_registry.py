import pytest
from src.mcp_integration.registry import get_agent_schema, update_agent_schema
from unittest.mock import patch


@pytest.mark.asyncio
async def test_mcp_registry_tools():
    with patch("src.mcp_integration.registry.registry_store") as mock_store:
        # Mock async methods properly
        async def mock_update_schema(*args, **kwargs):
            return None

        mock_store.update_schema = mock_update_schema

        res = await update_agent_schema("TestAgent", '{"type": "object"}')
        assert "updated successfully" in res

        res = await update_agent_schema("TestAgent", '{"type": "object"')
        assert "Invalid JSON" in res

        async def mock_get_schema_exist(*args, **kwargs):
            return '{"type": "object"}'

        mock_store.get_schema = mock_get_schema_exist

        schema = await get_agent_schema("TestAgent")
        assert schema == '{"type": "object"}'

        async def mock_get_schema_none(*args, **kwargs):
            return None

        mock_store.get_schema = mock_get_schema_none

        schema_beta = await get_agent_schema("Agent_Beta")
        assert schema_beta != "{}"

        schema_missing = await get_agent_schema("UnknownAgent")
        assert schema_missing == "{}"
