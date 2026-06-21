import os
import json
import datetime
import uuid
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv
from src.core.llm_factory import LLMFactory

load_dotenv()
console = Console()


class SelfHealingEngine:
    """
    Self-Healing Engine that repairs JSON payloads using LLM inference (LangChain).
    Implements a LangGraph node with Fallback Logic.
    """

    def __init__(self):
        # We will try providers based on the ENV configuration
        env_order = os.getenv("PROVIDER_ORDER")
        if env_order:
            self.providers = [
                p.strip().upper() for p in env_order.split(",") if p.strip()
            ]
        else:
            # Default fallback order if not specified
            self.providers = ["OPENAI", "LOCAL_OLLAMA", "ANTHROPIC", "GROQ"]

    async def repair_node(self, state: dict) -> dict:
        """
        LangGraph node execution for self-healing.
        """
        attempts = state.get("repair_attempts", 0)
        schema_json = state.get("schema_dict", {})
        malformed_data = state.get("payload", {})
        error_context = state.get("error_context", "Unknown Error")

        # Determine provider based on attempt count (Fallback mechanism)
        provider = self.providers[attempts % len(self.providers)]

        title = schema_json.get("title", "UnknownSchema")
        console.print(
            Panel(
                f"Target Schema: {title}\nError: {error_context}\nProvider: {provider}",
                title=f"[~] Healing Protocol Initiated (Attempt {attempts + 1})",
                border_style="yellow",
            )
        )
        console.print(
            f"[dim cyan][*] LLM Inference applied via {provider}...[/dim cyan]"
        )

        try:
            llm = LLMFactory.get_llm(provider)
            prompt = f"""
            You are a Semantic Healing Agent.
            Contract Schema: {json.dumps(schema_json)}
            Malformed Data: {json.dumps(malformed_data)}
            Validation Error: {error_context}

            Return ONLY the corrected JSON payload. Do not include markdown blocks or any text other than the valid JSON.
            """

            response = await llm.ainvoke(prompt)

            # Clean response text in case LLM added markdown backticks
            cleaned_text = response.content.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            healed_data = json.loads(cleaned_text)

            # Log the successful healing attempt to agent_decisions.json
            self._log_decision(title, error_context, provider)
            console.print(
                f"[bold green][+] Packet Healed Successfully by {provider}![/bold green]"
            )

            return {
                "payload": healed_data,
                "active_provider": provider,
                "repair_attempts": attempts + 1,
            }

        except Exception as e:
            console.print(
                f"[bold red][!] Healing Failed with {provider}. Error: {e}[/bold red]"
            )
            return {"active_provider": provider, "repair_attempts": attempts + 1}

    @staticmethod
    def _log_decision(title: str, error_context: str, provider: str):
        decision_id = f"DECISION-HEAL-{str(uuid.uuid4())[:8].upper()}"
        log_path = os.path.join(
            os.getcwd(), ".antigravity", "logs", "agent_decisions.json"
        )
        try:
            with open(log_path, "r") as f:
                logs = json.load(f)
        except Exception as e:
            console.print(
                f"[yellow][!] Could not read existing decision logs: {e}[/yellow]"
            )
            logs = []

        logs.append(
            {
                "id": decision_id,
                "timestamp": datetime.datetime.now().isoformat() + "Z",
                "action": f"Healed malformed JSON payload for {title} using {provider}",
                "reason": f"Validation Error: {error_context}",
            }
        )

        with open(log_path, "w") as f:
            json.dump(logs, f, indent=2)
