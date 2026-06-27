import pytest
import time
from unittest.mock import AsyncMock, patch
from src.skills.validation import SemanticValidator


@pytest.mark.asyncio
async def test_schema_cache_ttl():
    mock_mcp = AsyncMock()
    mock_mcp.fetch_schema.return_value = {"type": "object"}

    # Set TTL to 1 second
    import os

    with patch.dict(os.environ, {"SCHEMA_CACHE_TTL_SECONDS": "1"}):
        validator = SemanticValidator(mcp_client=mock_mcp)

        # First call should fetch
        await validator._get_schema("TestAgent")
        assert mock_mcp.fetch_schema.call_count == 1

        # Immediate second call should use cache
        await validator._get_schema("TestAgent")
        assert mock_mcp.fetch_schema.call_count == 1

        # Wait for TTL to expire
        time.sleep(1.1)

        # Third call should fetch again
        await validator._get_schema("TestAgent")
        assert mock_mcp.fetch_schema.call_count == 2


@pytest.mark.asyncio
async def test_clear_cache():
    mock_mcp = AsyncMock()
    mock_mcp.fetch_schema.return_value = {"type": "object"}

    validator = SemanticValidator(mcp_client=mock_mcp)

    # Fetch
    await validator._get_schema("Agent1")
    assert mock_mcp.fetch_schema.call_count == 1

    # Clear specific cache
    validator.clear_cache("Agent1")

    # Fetch again, should trigger network call
    await validator._get_schema("Agent1")
    assert mock_mcp.fetch_schema.call_count == 2

    # Fetch Agent2
    await validator._get_schema("Agent2")
    assert mock_mcp.fetch_schema.call_count == 3

    # Clear all caches
    validator.clear_cache()

    # Fetch Agent2 again
    await validator._get_schema("Agent2")
    assert mock_mcp.fetch_schema.call_count == 4
