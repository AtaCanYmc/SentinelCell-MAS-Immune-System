import asyncio
import aiomqtt
from rich.console import Console

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "IoTSensorTarget",
            "type": "object",
            "properties": {
                "temperature": {"type": "integer"},
                "humidity": {"type": "integer"},
            },
            "required": ["temperature", "humidity"],
        }


async def publish_malformed_sensor_data(broker_url: str, agent_id: str):
    """Simulates a dumb IoT sensor sending malformed JSON."""
    await asyncio.sleep(2)  # Wait for gateway to start

    # Missing quotes around humidity key, and temperature is a string
    malformed_payload = '{ "temperature": "twenty-two", humidity: 45 }'

    topic = f"sentinel/iot/{agent_id}/raw"
    console.print(
        f"\n[bold yellow][IoT Sensor] Publishing malformed data to {topic}[/bold yellow]"
    )
    console.print(f"[dim][IoT Sensor] Data: {malformed_payload}[/dim]")

    try:
        async with aiomqtt.Client(hostname=broker_url) as client:
            await client.publish(topic, malformed_payload)
    except Exception as e:
        console.print(f"[bold red][IoT Sensor] Failed to publish: {e}[/bold red]")


async def simulate_mqtt_sniffing():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine
    from src.gateways.mqtt_gateway import MQTTGateway

    broker = "test.mosquitto.org"
    agent_id = "sensor_alpha_01"

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    # 1. Start the MQTT Gateway
    gateway = MQTTGateway(orchestrator, broker_url=broker)
    gateway.start()

    # 2. Start the Malformed Sensor Publisher
    pub_task = asyncio.create_task(publish_malformed_sensor_data(broker, agent_id))

    # 3. Create a clean topic listener to verify output
    async def listen_for_clean_data():
        clean_topic = f"sentinel/iot/{agent_id}/clean"
        try:
            async with aiomqtt.Client(hostname=broker) as client:
                await client.subscribe(clean_topic)
                console.print(
                    f"[bold green][Clean Listener] Waiting for healed data on {clean_topic}...[/bold green]"
                )

                async for message in client.messages:
                    payload = message.payload.decode()
                    console.print(
                        "\n[bold green][Clean Listener] SUCCESS! Received perfectly healed JSON:[/bold green]"
                    )
                    console.print(f"[bold white]{payload}[/bold white]")
                    break  # Stop after receiving one message
        except Exception:
            pass

    listen_task = asyncio.create_task(listen_for_clean_data())

    # Wait for the simulation to finish
    await pub_task
    await listen_task

    await gateway.stop()


if __name__ == "__main__":
    asyncio.run(simulate_mqtt_sniffing())
