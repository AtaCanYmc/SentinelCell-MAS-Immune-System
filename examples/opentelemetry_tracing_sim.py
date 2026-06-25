import asyncio
import os
import json
from rich.console import Console

console = Console()


async def simulate_opentelemetry_tracing():
    # Force use of ConsoleSpanExporter by default if no OTLP is given
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""

    console.print(
        "[bold yellow]--- Testing OpenTelemetry Distributed Tracing ---[/bold yellow]"
    )
    console.print(
        "[dim]This simulation will invoke the Orchestrator with tracing enabled and print Span outputs.[/dim]"
    )

    from src.agents.validator_agent import SentinelCell
    from src.core.tracer import get_tracer, inject_trace_context

    sentinel = SentinelCell()
    tracer = get_tracer()

    # 1. Simulate an Ingress message with its own root span
    dummy_payload = {"status": "valid", "nested": {"key": "value"}}

    with tracer.start_as_current_span("Ingress.SimulatedGateway") as ingress_span:
        ingress_span.set_attribute("message.source", "AgentAlpha")
        ingress_span.set_attribute("message.target", "AgentBeta")

        # Inject context to pass to orchestrator
        envelope = {
            "source": "AgentAlpha",
            "target": "AgentBeta",
            "payload": json.dumps(dummy_payload),
        }
        inject_trace_context(envelope)

        console.print(
            f"\n[cyan][+] Ingress Context Injected: {envelope.get('traceparent')}[/cyan]"
        )

        # 2. Invoke Orchestrator (passing the envelope context)
        console.print("\n[yellow][~] Invoking Orchestrator...[/yellow]")
        result = await sentinel.intercept(
            source=envelope["source"],
            target=envelope["target"],
            payload=envelope["payload"],
            context=envelope,  # pass the dictionary to extract context
        )

        if result:
            console.print(f"\n[green][+] Result from Orchestrator: {result}[/green]")
        else:
            console.print("\n[red][!] Orchestrator rejected the payload.[/red]")

    # Allow time for BatchSpanProcessor to flush Console outputs
    console.print("\n[dim]Flushing OTel Spans...[/dim]")
    await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(simulate_opentelemetry_tracing())
