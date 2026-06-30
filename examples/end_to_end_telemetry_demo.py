import asyncio
import json
from rich.console import Console
from rich.panel import Panel

from util import setup_mock_environment, shutdown_sentinel

setup_mock_environment()

from src.agents.validator_agent import SentinelCell  # noqa: E402
from src.core.tracer import get_tracer, inject_trace_context  # noqa: E402

console = Console()


async def demo_end_to_end_telemetry():
    console.print(
        Panel.fit("[bold cyan]📡 End-to-End Telemetry Trace Demo 📡[/bold cyan]")
    )
    console.print(
        "[dim]Demonstrates that a Trace ID from the Gateway propagates all the way through the Healing Engine.[/dim]"
    )

    sentinel = SentinelCell()
    tracer = get_tracer()

    try:
        # Start the "Gateway" root span
        with tracer.start_as_current_span("FastAPI.Gateway.Ingress") as gateway_span:
            gateway_span.set_attribute("http.method", "POST")

            # 1. Prepare Envelope with Trace Context injected
            envelope = {
                "source": "Agent_Alpha",
                "target": "Agent_Beta",
                "payload": json.dumps({"status": "error"}),  # Missing 'message'
            }
            inject_trace_context(envelope)

            traceparent = envelope.get("traceparent", "Unknown")
            console.print(
                f"\n[yellow][*] Injected Traceparent at Gateway:[/yellow] [cyan]{traceparent}[/cyan]"
            )

            # 2. Pass envelope to Sentinel
            console.print(
                "\n[yellow][*] Routing payload through SentinelCell...[/yellow]"
            )
            result = await sentinel.intercept(
                source=envelope["source"],
                target=envelope["target"],
                payload=envelope["payload"],
                context=envelope,
            )

            # 3. Output
            console.print(f"\n[green][+] Orchestrator Output:[/green] {result}")
            console.print(
                "[dim]The OpenTelemetry spans exported to the console should all share the same trace_id as the gateway.[/dim]"
            )

        # Give time for OTel batch processor to flush
        await asyncio.sleep(2)

        console.print("\n[bold green]✅ Telemetry Trace Demo Complete![/bold green]")
    finally:
        await shutdown_sentinel(sentinel)


if __name__ == "__main__":
    asyncio.run(demo_end_to_end_telemetry())
