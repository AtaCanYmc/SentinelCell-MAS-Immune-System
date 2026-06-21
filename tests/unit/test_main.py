import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
@patch("src.main.SentinelCell")
@patch("src.main.asyncio.sleep", new_callable=AsyncMock)
async def test_main(mock_sleep, mock_sentinel_class):
    mock_sentinel_instance = mock_sentinel_class.return_value
    mock_sentinel_instance.intercept = AsyncMock()

    from src.main import main

    await main()

    # Check that intercepts were called
    assert mock_sentinel_instance.intercept.call_count == 3
