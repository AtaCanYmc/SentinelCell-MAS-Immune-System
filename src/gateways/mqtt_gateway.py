import asyncio
import aiomqtt
import orjson
from src.core.logger import get_console

console = get_console()


class MQTTGateway:
    """
    Edge & IoT Ready MQTT Sniffer for SentinelCell.
    Passively monitors MQTT traffic, intercepts malformed payloads,
    cleans them using the Self-Healing Engine, and republishes them.
    """

    def __init__(
        self, orchestrator, broker_url: str = "test.mosquitto.org", port: int = 1883
    ):
        self.orchestrator = orchestrator
        self.broker_url = broker_url
        self.port = port
        self.client = None
        self._task = None

    async def _run(self):
        try:
            async with aiomqtt.Client(
                hostname=self.broker_url, port=self.port
            ) as client:
                self.client = client
                # Subscribe to wildcard raw topics (e.g. sentinel/iot/temperature_sensor/raw)
                topic_pattern = "sentinel/iot/+/raw"
                await client.subscribe(topic_pattern)
                console.print(
                    f"[bold cyan][IoT Gateway] Connected to {self.broker_url}:{self.port}[/bold cyan]"
                )
                console.print(
                    f"[bold cyan][IoT Gateway] Sniffing topic: {topic_pattern}[/bold cyan]"
                )

                async for message in client.messages:
                    topic = str(message.topic)
                    payload = message.payload.decode()

                    # Extract agent source from topic string (e.g., sentinel/iot/agent_name/raw)
                    parts = topic.split("/")
                    if len(parts) >= 4:
                        agent_source = parts[2]
                    else:
                        agent_source = "unknown_iot_device"

                    console.print(
                        f"\n[dim][IoT Gateway] Received from {agent_source}: {payload}[/dim]"
                    )

                    # Intercept via SentinelCell
                    # Target is generally inferred or hardcoded for IoT, let's just use 'iot_target'
                    target = "iot_target"

                    # Run intercept logic
                    clean_payload = await self.orchestrator.intercept(
                        agent_source, target, payload
                    )

                    if clean_payload:
                        # Republish clean data
                        clean_topic = f"sentinel/iot/{agent_source}/clean"

                        # Serialize if dict
                        if isinstance(clean_payload, dict):
                            out_data = orjson.dumps(clean_payload).decode("utf-8")
                        else:
                            out_data = str(clean_payload)

                        await client.publish(clean_topic, out_data)
                        console.print(
                            f"[bold green][IoT Gateway] Republished clean data to {clean_topic}[/bold green]"
                        )
        except Exception as e:
            console.print(f"[bold red][IoT Gateway] Error: {e}[/bold red]")

    def start(self):
        """Starts the MQTT listener loop in the background."""
        self._task = asyncio.create_task(self._run())
        return self._task

    async def stop(self):
        """Stops the MQTT listener loop."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            console.print("[dim][IoT Gateway] Shut down.[/dim]")
