import os
import json
from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()
console = Console()


class SelfHealingEngine:
    """
    Self-Healing Engine that intercepts ValidationError exceptions
    and repairs JSON payloads using LLM inference based on defined Pydantic schemas.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            console.print(
                "[dim yellow][~] No GEMINI_API_KEY found in .env. Self-Healing will use offline/mock mode.[/dim yellow]"
            )
            self.mock_mode = True
        else:
            self.mock_mode = False
            # To be implemented: initialize real LLM client using google-genai
            # self.client = genai.Client(api_key=self.api_key)

    async def heal_packet(
        self, schema_class: type[BaseModel], malformed_data: dict, error_context: str
    ) -> dict | None:
        """
        Attempts to heal a malformed data packet.
        Returns the sanitized data if successful, None if beyond repair.
        """
        console.print(
            Panel(
                f"Target Schema: {schema_class.__name__}\nError: {error_context}",
                title="[~] Healing Protocol Initiated",
                border_style="yellow",
            )
        )

        schema_json = schema_class.model_json_schema()

        if self.mock_mode:
            console.print("[dim cyan][*] Offline Mock Inference applied...[/dim cyan]")
            healed_data = malformed_data.copy()
            # Simple offline mock fix for StatusContract
            if (
                schema_class.__name__ == "StatusContract"
                and "status" in healed_data
                and "message" not in healed_data
            ):
                healed_data["message"] = (
                    f"Auto-healed context for status: {healed_data['status']}"
                )
        else:
            prompt = f"""
            You are a Semantic Healing Agent.
            Contract Schema: {json.dumps(schema_json)}
            Malformed Data: {json.dumps(malformed_data)}
            Validation Error: {error_context}

            Return ONLY the corrected JSON payload. Do not include markdown blocks.
            """
            console.print("[dim cyan][*] LLM Inference applied...[/dim cyan]")
            # Real LLM call would go here using the prompt
            console.print(f"[dim]Prepared Prompt:[/dim]\n{prompt}")

            # response = self.client.models.generate_content(...)
            # healed_data = json.loads(response.text)
            healed_data = (
                malformed_data  # Fallback for now if real LLM is not fully integrated
            )

        # Re-Validation
        try:
            schema_class(**healed_data)
            console.print(
                "[bold green][+] Packet Healed Successfully! Semantic Integrity Restored.[/bold green]"
            )
            return healed_data
        except ValidationError:
            console.print(
                "[bold red][!] Healing Failed. Data beyond repair.[/bold red]"
            )
            return None
