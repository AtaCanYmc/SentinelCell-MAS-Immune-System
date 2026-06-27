import json
import asyncio
from src.core.broker_factory import BrokerFactory
from src.core.tracer import get_tracer, inject_trace_context, extract_trace_context
from src.agents.validator_agent import SentinelCell
from rich.console import Console

console = Console()


async def mq_worker():
    broker = BrokerFactory.get_broker()
    sentinel = SentinelCell()
    tracer = get_tracer()

    console.print("[bold cyan]SentinelCell Ingress MQ Worker started...[/bold cyan]")

    while True:
        try:
            # broker.consume blocks until a message is available
            data_str = await broker.consume("sentinel.in", timeout=0)
            if data_str:
                # We expect the payload to be wrapped with source and target info for routing
                # Example: {"source": "AgentA", "target": "AgentB", "payload": "{\"status\":\"ok\"}"}
                try:
                    envelope = json.loads(data_str)
                    # OpenTelemetry Trace Context Extraction
                    context = extract_trace_context(envelope)

                    with tracer.start_as_current_span(
                        "IngressMQ.Process", context=context
                    ) as span:
                        source = envelope.get("source", "Unknown")
                        target = envelope.get("target", "Unknown")
                        payload = envelope.get("payload", data_str)

                        span.set_attribute("message.source", source)
                        span.set_attribute("message.target", target)

                        if isinstance(payload, dict):
                            payload = json.dumps(payload)

                        # We pass the traceparent along with the payload to orchestrator?
                        # The orchestrator is invoked via `sentinel.intercept`. We can inject context into it.
                        # Since we are using an object in memory, it might share context implicitly if in same thread.
                        # But for real async/distributed, we pass it inside the payload or kwargs.
                        # For SentinelCell intercept, we can pass context inside the payload dict if it was a dict,
                        # but payload is string. Let's let the tracer context handle it automatically via OTel async context.

                        result = await sentinel.intercept(
                            source=source, target=target, payload=payload
                        )

                        if result:
                            # Inject trace context to result before pushing
                            if isinstance(result, str):
                                try:
                                    res_dict = json.loads(result)
                                    inject_trace_context(res_dict)
                                    result = json.dumps(res_dict)
                                except Exception as e:
                                    console.print(
                                        f"[dim yellow]Warning: Failed to inject trace context into string payload: {e}[/dim yellow]"
                                    )
                            elif isinstance(result, dict):
                                inject_trace_context(result)

                            # Push the valid/healed message to 'sentinel.out'
                            await broker.push(
                                "sentinel.out",
                                result
                                if isinstance(result, str)
                                else json.dumps(result),
                            )
                            console.print(
                                "[green]Message processed and forwarded to sentinel.out[/green]"
                            )
                        else:
                            span.set_attribute("error", True)
                            console.print("[red]Message rejected and dropped.[/red]")

                except json.JSONDecodeError:
                    console.print(
                        "[red]Invalid envelope format. Dropping message.[/red]"
                    )

        except Exception as e:
            console.print(f"[bold red]Worker Error: {e}[/bold red]")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(mq_worker())
