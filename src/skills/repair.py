import os
import json
import uuid
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv
from src.core.llm_factory import LLMFactory
from src.core.broadcaster import broadcaster

try:
    import chromadb

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

load_dotenv()
console = Console()


class SelfHealingEngine:
    """
    Self-Healing Engine that repairs JSON payloads using LLM inference (LangChain)
    and an Adaptive Learning Feedback Loop via VectorDB (ChromaDB).
    """

    def __init__(self):
        env_order = os.getenv("PROVIDER_ORDER")
        if env_order:
            self.providers = [
                p.strip().upper() for p in env_order.split(",") if p.strip()
            ]
        else:
            self.providers = ["OPENAI", "LOCAL_OLLAMA", "ANTHROPIC", "GROQ"]

        self.chroma_client = None
        self.collection = None

        if CHROMA_AVAILABLE:
            try:
                db_path = os.path.join(os.getcwd(), "chroma_db")
                self.chroma_client = chromadb.PersistentClient(path=db_path)
                self.collection = self.chroma_client.get_or_create_collection(
                    name="healing_memory"
                )
                console.print(
                    "[dim green][+] Adaptive Learning (ChromaDB) Initialized[/dim green]"
                )
            except Exception as e:
                console.print(f"[dim yellow][!] ChromaDB Init Failed: {e}[/dim yellow]")

    async def repair_node(self, state: dict) -> dict:
        attempts = state.get("repair_attempts", 0)
        schema_json = state.get("schema_dict", {})
        malformed_data = state.get("payload", {})
        error_context = state.get("error_context", "Unknown Error")

        provider = self.providers[attempts % len(self.providers)]
        title = schema_json.get("title", "UnknownSchema")

        console.print(
            Panel(
                f"Target Schema: {title}\nError: {error_context}\nProvider: {provider}",
                title=f"[~] Healing Protocol Initiated (Attempt {attempts + 1})",
                border_style="yellow",
            )
        )
        await broadcaster.broadcast(
            "HEAL_START",
            f"Attempt {attempts + 1} | Provider: {provider} | Error: {error_context}",
        )

        # RAG / Adaptive Learning: Query VectorDB for past experiences
        past_experience = ""
        if self.collection:
            try:
                query_str = f"Error: {error_context} Schema: {title}"
                results = self.collection.query(query_texts=[query_str], n_results=1)
                if results["documents"] and results["documents"][0]:
                    best_match = results["documents"][0][0]
                    # Inject into prompt
                    past_experience = f"\nPast Experience Found in ChromaDB:\n{best_match}\nUse this as a reference to fix the payload faster and avoid hallucination."
                    console.print(
                        "[cyan][*] Past Experience Retrieved from VectorDB[/cyan]"
                    )
            except Exception as e:
                console.print(
                    f"[dim yellow][!] Memory Retrieval Failed: {e}[/dim yellow]"
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
            {past_experience}

            Return ONLY the corrected JSON payload. Do not include markdown blocks or any text other than the valid JSON.
            """

            response = await llm.ainvoke(prompt)

            # Clean response text
            cleaned_text = response.content.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            healed_data = json.loads(cleaned_text)

            # Logging & Adaptive Learning (Save to VectorDB)
            self._log_decision(title, error_context, provider)

            if self.collection:
                try:
                    doc_id = f"mem-{uuid.uuid4()}"
                    memory_doc = f"Error: {error_context} | Malformed: {json.dumps(malformed_data)} | Fixed: {json.dumps(healed_data)}"
                    self.collection.add(
                        documents=[memory_doc],
                        metadatas=[{"schema": title, "provider": provider}],
                        ids=[doc_id],
                    )
                    console.print(
                        "[dim magenta][+] New experience saved to VectorDB[/dim magenta]"
                    )
                except Exception as e:
                    console.print(
                        f"[dim yellow][!] Memory Save Failed: {e}[/dim yellow]"
                    )

            console.print(
                f"[bold green][+] Packet Healed Successfully by {provider}![/bold green]"
            )
            await broadcaster.broadcast(
                "HEAL_SUCCESS",
                f"Fixed payload using {provider}: {json.dumps(healed_data)}",
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
            await broadcaster.broadcast("HEAL_FAIL", f"Provider {provider} failed: {e}")
            return {"active_provider": provider, "repair_attempts": attempts + 1}

    @staticmethod
    def _log_decision(title: str, error_context: str, provider: str):
        import time
        from src.core.telemetry import OpenTelemetryLog, OTelResource

        decision_id = f"DECISION-HEAL-{str(uuid.uuid4())[:8].upper()}"
        log_path = os.path.join(
            os.getcwd(), ".antigravity", "logs", "agent_decisions.json"
        )
        try:
            with open(log_path, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []

        # Enforce strict OpenTelemetry standard via Pydantic Schema
        otel_log = OpenTelemetryLog(
            Timestamp=int(time.time() * 1e9),
            TraceId=uuid.uuid4().hex,
            SpanId=uuid.uuid4().hex[:16],
            TraceFlags=1,
            SeverityText="INFO",
            SeverityNumber=9,
            Body="Healed malformed JSON payload",
            Resource=OTelResource(
                attributes={"service.name": "SentinelCell.ImmuneSystem"}
            ),
            Attributes={
                "decision.id": decision_id,
                "target.schema": title,
                "llm.provider": provider,
                "validation.error": error_context,
            },
        )

        logs.append(otel_log.model_dump())

        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w") as f:
            json.dump(logs, f, indent=2)
