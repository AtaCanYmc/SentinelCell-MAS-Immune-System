import os
import orjson
import uuid
from rich.panel import Panel
from dotenv import load_dotenv
from src.core.llm_factory import LLMFactory
from src.core.prompt_manager import PromptManager
from src.core.broadcaster import broadcaster
from src.core.memory_factory import MemoryFactory
from src.core.tracer import get_tracer, shutdown_tracer
from src.core.logger import get_console

tracer = get_tracer()

load_dotenv()
console = get_console()


class SelfHealingEngine:
    """
    Self-Healing Engine that repairs JSON payloads using LLM inference (LangChain)
    and an Adaptive Learning Feedback Loop via VectorDB (ChromaDB).
    """

    def __init__(self, sandbox=False):
        self.sandbox = sandbox
        env_order = os.getenv("PROVIDER_ORDER")
        if env_order:
            self.providers = [
                p.strip().upper() for p in env_order.split(",") if p.strip()
            ]
        else:
            self.providers = ["OPENAI", "LOCAL_OLLAMA", "ANTHROPIC", "GROQ"]

        self.memory = None
        if not self.sandbox:
            try:
                self.memory = MemoryFactory.get_memory_store()
                console.print(
                    f"[dim green][+] Adaptive Learning ({self.memory.__class__.__name__}) Initialized[/dim green]"
                )
            except Exception as e:
                console.print(f"[dim yellow][!] Memory Init Failed: {e}[/dim yellow]")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    async def aclose(self):
        await broadcaster.shutdown()
        if self.memory and hasattr(self.memory, "close"):
            await self.memory.close()
        shutdown_tracer()

    async def repair_node(self, state):
        attempts = state.get("repair_attempts", 0)
        schema_json = state.get("schema_dict") or {}
        malformed_data = state.get("payload", {})
        attempts = state.get("repair_attempts", 0)
        provider = self.providers[attempts % len(self.providers)]
        title = schema_json.get("title", "UnknownSchema")

        import time
        import os
        import hashlib
        import redis.asyncio as redis

        # Semantic Caching
        payload_hash = hashlib.sha256(
            orjson.dumps(malformed_data, option=orjson.OPT_SORT_KEYS)
        ).hexdigest()
        cache_key = f"sentinel:semantic_cache:{title}:{payload_hash}"
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                async with redis.from_url(redis_url) as r:
                    cached_repair = await r.get(cache_key)
                    if cached_repair:
                        console.print(
                            "[bold green][*] SEMANTIC CACHE HIT! Bypassing LLM. Latency: 1ms[/bold green]"
                        )
                        return {
                            "payload": orjson.loads(cached_repair),
                            "active_provider": "CACHE",
                            "repair_attempts": attempts,
                            "last_memory_id": None,
                        }
            except Exception:
                pass
        else:
            if not hasattr(self, "_semantic_cache"):
                self._semantic_cache = {}
            if cache_key in self._semantic_cache:
                console.print(
                    "[bold green][*] SEMANTIC CACHE HIT! Bypassing LLM. Latency: 1ms[/bold green]"
                )
                return {
                    "payload": self._semantic_cache[cache_key],
                    "active_provider": "CACHE",
                    "repair_attempts": attempts,
                    "last_memory_id": None,
                }
        rate_limit = int(os.getenv("LLM_RATE_LIMIT_PER_MIN", "50"))
        current_min = int(time.time() / 60)

        if redis_url:
            try:
                async with redis.from_url(redis_url) as r:
                    key = f"sentinel:llm_rate_limit:{current_min}"
                    count = await r.incr(key)
                    if count == 1:
                        await r.expire(key, 60)
                    if count > rate_limit:
                        console.print(
                            f"[bold red][!] LLM Rate Limit Exceeded ({count} > {rate_limit}/min). Dropping repair.[/bold red]"
                        )
                        return {
                            "is_valid": False,
                            "error_context": "LLM Rate Limit Exceeded",
                            "repair_attempts": attempts + 1,
                        }
            except Exception:
                pass
        else:
            if not hasattr(self, "_local_rate_limit"):
                self._local_rate_limit = {}
            if current_min not in self._local_rate_limit:
                self._local_rate_limit = {current_min: 0}

            self._local_rate_limit[current_min] += 1
            count = self._local_rate_limit[current_min]

            if count > rate_limit:
                console.print(
                    f"[bold red][!] LLM Rate Limit Exceeded ({count} > {rate_limit}/min). Dropping repair.[/bold red]"
                )
                return {
                    "is_valid": False,
                    "error_context": "LLM Rate Limit Exceeded",
                    "repair_attempts": attempts + 1,
                }

        error_context = state.get("error_context", "Unknown Error")

        malformed_str = orjson.dumps(malformed_data).decode("utf-8")
        malformed_str = malformed_str.replace(
            "---START UNTRUSTED DATA---", "[REDACTED_BOUNDARY]"
        )
        malformed_str = malformed_str.replace(
            "---END UNTRUSTED DATA---", "[REDACTED_BOUNDARY]"
        )

        # --- ADAPTIVE UNLEARNING ---
        # If we are here and have a last_memory_id, it means the previous fix failed the validator!
        # We must "Unlearn" the hallucination from VectorDB.
        last_memory_id = state.get("last_memory_id")
        if last_memory_id and self.memory:
            try:
                self.memory.delete_memory(last_memory_id)
                console.print(
                    f"[bold red][!] UNLEARNING: Hallucinated repair {last_memory_id} deleted from VectorDB[/bold red]"
                )
            except Exception as e:
                console.print(f"[dim yellow][!] Unlearning Failed: {e}[/dim yellow]")

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
        if self.memory:
            try:
                query_str = f"Error: {error_context} Schema: {title}"
                best_match = self.memory.query_memory(query_str)
                if best_match:
                    # Inject into prompt
                    past_experience = f"\nPast Experience Found in VectorDB:\n{best_match}\nUse this as a reference to fix the payload faster and avoid hallucination."
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
            prompt = PromptManager.render(
                "repair.jinja2",
                {
                    "target": title,
                    "schema": orjson.dumps(schema_json).decode("utf-8"),
                    "error_context": error_context,
                    "past_experience": past_experience,
                    "payload": malformed_str,
                },
            )

            with tracer.start_as_current_span("LLM.Inference") as span:
                span.set_attribute("llm.provider", provider)
                try:
                    response = await llm.ainvoke(prompt)
                    span.set_attribute("llm.success", True)
                except Exception as e:
                    span.record_exception(e)
                    span.set_attribute("llm.success", False)
                    raise

            # Clean response text
            cleaned_text = response.content.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            healed_data = orjson.loads(cleaned_text)

            # --- DUAL-LAYER SEMANTIC DRIFT GUARD ---
            def check_numeric_drift(orig, new, path="root"):
                if isinstance(orig, dict) and isinstance(new, dict):
                    for k, v in orig.items():
                        if k in new:
                            check_numeric_drift(v, new[k], path + f".{k}")
                elif isinstance(orig, list) and isinstance(new, list):
                    for i, (v1, v2) in enumerate(zip(orig, new)):
                        check_numeric_drift(v1, v2, path + f"[{i}]")
                elif isinstance(orig, (int, float, str)) and not isinstance(orig, bool):
                    try:
                        orig_num = float(orig)
                        is_orig_num = True
                    except (ValueError, TypeError):
                        is_orig_num = False

                    if is_orig_num:
                        try:
                            new_num = float(new)
                            is_new_num = True
                        except (ValueError, TypeError):
                            is_new_num = False

                        if not is_new_num:
                            raise ValueError(
                                f"Numeric Semantic Drift: Type changed at {path}"
                            )
                        if orig_num != new_num:
                            raise ValueError(
                                f"Numeric Semantic Drift: Value changed at {path} ({orig} -> {new})"
                            )

            def extract_values(obj):
                if isinstance(obj, dict):
                    return sum((extract_values(v) for v in obj.values()), [])
                elif isinstance(obj, list):
                    return sum((extract_values(v) for v in obj), [])
                else:
                    return [str(obj).lower()]

            if "_raw_unparsed_payload" not in malformed_data:
                # 1. Type-Aware Numeric Guard
                try:
                    check_numeric_drift(malformed_data, healed_data)
                except ValueError as e:
                    console.print(f"[bold red][!] {e}[/bold red]")
                    raise

                # 2. Jaccard Similarity Guard
                orig_vals = set(extract_values(malformed_data))
                new_vals = set(extract_values(healed_data))
                if orig_vals:
                    intersection = orig_vals.intersection(new_vals)
                    similarity = len(intersection) / len(orig_vals)
                    if similarity < float(os.getenv("SEMANTIC_DRIFT_THRESHOLD", "0.3")):
                        console.print(
                            f"[bold red][!] SEMANTIC DRIFT DETECTED! Value retention: {similarity * 100:.1f}%. Rejecting repair.[/bold red]"
                        )
                        raise ValueError(
                            f"Semantic Drift: Payload lost critical original values. Retention: {similarity:.2f}"
                        )

            # Logging & Adaptive Learning (Save to VectorDB)
            if not self.sandbox:
                self._log_decision(title, error_context, provider)

            new_memory_id = None
            if self.memory and not self.sandbox:
                try:
                    import time

                    doc_id = f"mem-{uuid.uuid4()}"
                    memory_doc = f"Error: {error_context} | Malformed: {orjson.dumps(malformed_data).decode('utf-8')} | Fixed: {orjson.dumps(healed_data).decode('utf-8')}"
                    self.memory.add_memory(
                        doc_id=doc_id,
                        memory_doc=memory_doc,
                        metadata={
                            "schema": title,
                            "provider": provider,
                            "timestamp": time.time(),
                        },
                    )
                    new_memory_id = doc_id
                    console.print(
                        "[dim magenta][+] New experience saved to VectorDB[/dim magenta]"
                    )
                except Exception as e:
                    console.print(
                        f"[dim yellow][!] Memory Save Failed: {e}[/dim yellow]"
                    )

            # Save to Semantic Cache
            if redis_url:
                try:
                    async with redis.from_url(redis_url) as r:
                        await r.setex(
                            cache_key, 3600, orjson.dumps(healed_data).decode("utf-8")
                        )
                except Exception:
                    pass
            else:
                if not hasattr(self, "_semantic_cache"):
                    self._semantic_cache = {}
                self._semantic_cache[cache_key] = healed_data

            console.print(
                f"[bold green][+] Packet Healed Successfully by {provider}![/bold green]"
            )
            await broadcaster.broadcast(
                "HEAL_SUCCESS",
                f"Fixed payload using {provider}: {orjson.dumps(healed_data).decode('utf-8')}",
            )

            return {
                "payload": healed_data,
                "active_provider": provider,
                "repair_attempts": attempts + 1,
                "last_memory_id": new_memory_id,
            }

        except Exception as e:
            console.print(
                f"[bold red][!] Healing Failed with {provider}. Error: {e}[/bold red]"
            )
            await broadcaster.broadcast("HEAL_FAIL", f"Provider {provider} failed: {e}")
            return {
                "active_provider": provider,
                "repair_attempts": attempts + 1,
                "last_memory_id": None,
            }

    @staticmethod
    def _log_decision(title: str, error_context: str, provider: str):
        import time
        from opentelemetry import trace
        from src.core.telemetry import OpenTelemetryLog, OTelResource

        decision_id = f"DECISION-HEAL-{str(uuid.uuid4())[:8].upper()}"
        log_path = os.path.join(os.getcwd(), "logs", "agent_decisions.json")
        try:
            with open(log_path, "r") as f:
                logs = orjson.loads(f.read())
        except Exception:
            logs = []

        # Propagate active trace context
        span = trace.get_current_span()
        span_context = span.get_span_context() if span else None
        if span_context and span_context.is_valid:
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")
        else:
            trace_id = uuid.uuid4().hex
            span_id = uuid.uuid4().hex[:16]

        # Enforce strict OpenTelemetry standard via Pydantic Schema
        otel_log = OpenTelemetryLog(
            Timestamp=int(time.time() * 1e9),
            TraceId=trace_id,
            SpanId=span_id,
            TraceFlags=1,
            SeverityText="INFO",
            SeverityNumber=9,
            Body="Healed malformed JSON payload",
            Resource=OTelResource(
                attributes={
                    "service.name": "SentinelCell.ImmuneSystem",
                    "deployment.environment": os.getenv("ENVIRONMENT", "production"),
                    "k8s.pod.name": os.getenv("HOSTNAME", "local"),
                }
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
            f.write(orjson.dumps(logs, option=orjson.OPT_INDENT_2).decode("utf-8"))
