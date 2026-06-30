import os
import json
import asyncio
from rich.panel import Panel

from src.core.llm_factory import LLMFactory
from src.mcp_integration.client import SchemaRegistryClient
from src.core.tracer import get_tracer
from src.core.prompt_manager import PromptManager
from src.core.logger import get_console

console = get_console()
tracer = get_tracer()


class AutoSchemaInferencer:
    def __init__(self, mcp_client: SchemaRegistryClient, on_schema_registered_cb=None):
        self.mcp_client = mcp_client
        self.on_schema_registered_cb = on_schema_registered_cb
        self.threshold = int(os.getenv("OBSERVATION_THRESHOLD", "5"))
        self._observations = {}  # { agent_target: [payload_dict1, payload_dict2, ...] }
        self._inferring = (
            set()
        )  # To prevent multiple concurrent inferences for same agent
        self.provider = os.getenv("PROVIDER_ORDER", "OPENAI").split(",")[0].strip()
        self.llm = LLMFactory.get_llm(self.provider)

    def observe(self, agent_target: str, data: dict):
        """
        Observes a payload that bypassed validation because of missing schema.
        If threshold is reached, triggers asynchronous schema inference.
        """
        if agent_target in self._inferring:
            return  # Already inferring for this target

        if agent_target not in self._observations:
            self._observations[agent_target] = []

        self._observations[agent_target].append(data)

        if len(self._observations[agent_target]) >= self.threshold:
            # We reached the threshold, move the observed data and start inferring
            payloads_to_infer = self._observations.pop(agent_target)
            self._inferring.add(agent_target)

            # Start inference in the background
            asyncio.create_task(
                self._infer_and_register_task(agent_target, payloads_to_infer)
            )

    async def _infer_and_register_task(self, agent_target: str, payloads: list[dict]):
        """
        Background task to use LLM to infer schema and register it.
        """
        with tracer.start_as_current_span("AutoSchema.Inference") as span:
            span.set_attribute("agent.target", agent_target)
            span.set_attribute("observation.count", len(payloads))

            console.print(
                Panel.fit(
                    f"[bold yellow]🔍 Auto-Schema Inference Triggered[/bold yellow]\n"
                    f"Agent: [cyan]{agent_target}[/cyan]\n"
                    f"Observed Payloads: {len(payloads)}",
                    border_style="yellow",
                )
            )

            schema_dict = await self._generate_schema_from_llm(agent_target, payloads)

            if schema_dict:
                # Register to MCP
                success = await self.mcp_client.register_schema(
                    agent_target, schema_dict
                )
                if success:
                    span.set_attribute("schema.registered", True)
                    console.print(
                        f"[bold green]✅ Auto-Schema registered successfully for {agent_target}[/bold green]"
                    )
                    if self.on_schema_registered_cb:
                        self.on_schema_registered_cb(agent_target)
                else:
                    span.set_attribute("schema.registered", False)
                    console.print(
                        f"[bold red]❌ Failed to register inferred schema for {agent_target}[/bold red]"
                    )
            else:
                span.set_attribute("error", True)
                console.print(
                    f"[bold red]❌ LLM failed to infer schema for {agent_target}[/bold red]"
                )

            self._inferring.discard(agent_target)

    async def _generate_schema_from_llm(
        self, agent_target: str, payloads: list[dict]
    ) -> dict | None:
        """
        Prompts the LLM to generate a strict JSON Schema Draft 7 from the payloads.
        """
        prompt = PromptManager.render(
            "schema_inference.jinja2",
            {"target": agent_target, "payloads": json.dumps(payloads, indent=2)},
        )
        response = await self.llm.ainvoke(prompt)
        try:
            # Strip markdown if LLM returned it anyway
            cleaned = response.content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            schema = json.loads(cleaned.strip())
            return schema
        except Exception as e:
            console.print(f"[red]Error parsing LLM schema inference: {e}[/red]")
            console.print(f"[dim]LLM Output:[/dim]\n{response}")
            return None
