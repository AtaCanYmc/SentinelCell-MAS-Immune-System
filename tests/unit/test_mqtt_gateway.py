import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.gateways.mqtt_gateway import MQTTGateway


class AsyncIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


@pytest.mark.asyncio
async def test_mqtt_gateway_flow():
    # Setup mock messages
    mock_msg1 = MagicMock()
    mock_msg1.topic = "sentinel/iot/agent_x/raw"
    mock_msg1.payload = b"dirty_payload_1"

    mock_msg2 = MagicMock()
    mock_msg2.topic = "sentinel/iot/agent_y/raw"
    mock_msg2.payload = b"dirty_payload_2"

    messages = [mock_msg1, mock_msg2]

    # Mock client and its behavior
    mock_client = MagicMock()
    mock_client.subscribe = AsyncMock()
    mock_client.publish = AsyncMock()
    mock_client.messages = AsyncIterator(messages)

    # Mock aiomqtt Client context manager
    mock_client_context = MagicMock()
    mock_client_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_context.__aexit__ = AsyncMock(return_value=None)

    # Mock orchestrator
    mock_orchestrator = MagicMock()
    # Intercept returns clean data or dict
    mock_orchestrator.intercept = AsyncMock(
        side_effect=lambda src, target, payload: (
            {"cleaned": True} if src == "agent_x" else "cleaned_string"
        )
    )

    with patch("aiomqtt.Client", return_value=mock_client_context):
        gateway = MQTTGateway(mock_orchestrator, broker_url="localhost", port=1883)
        gateway.start()

        # Give event loop time to process the task
        await asyncio.sleep(0.1)

        # Stop gateway
        await gateway.stop()

        # Check subscription
        mock_client.subscribe.assert_called_with("sentinel/iot/+/raw")

        # Check intercept calls
        assert mock_orchestrator.intercept.call_count == 2
        mock_orchestrator.intercept.assert_any_call(
            "agent_x", "iot_target", "dirty_payload_1"
        )
        mock_orchestrator.intercept.assert_any_call(
            "agent_y", "iot_target", "dirty_payload_2"
        )

        # Check publishes
        assert mock_client.publish.call_count == 2
        # First call (agent_x) published a dict as JSON
        mock_client.publish.assert_any_call(
            "sentinel/iot/agent_x/clean", '{"cleaned":true}'
        )
        # Second call (agent_y) published a string
        mock_client.publish.assert_any_call(
            "sentinel/iot/agent_y/clean", "cleaned_string"
        )
