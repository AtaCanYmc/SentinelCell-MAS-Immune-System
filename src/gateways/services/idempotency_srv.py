import os
import time
import asyncio
import orjson
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from src.core.logger import get_console

console = get_console()


class IdempotencyService:
    @staticmethod
    async def handle_idempotency(r, x_idempotency_key: str):
        """
        Handles Redis-based idempotency checks.
        Returns JSONResponse if a duplicate is found (or was processed),
        otherwise returns None.
        """
        idem_key = f"idempotency:{x_idempotency_key}"
        try:
            # ATOMIC SET NX: If it returns True, we are the ones processing
            was_set = await r.set(idem_key, "PROCESSING", ex=120, nx=True)

            if not was_set:
                channel = f"sentinel:idem:channel:{x_idempotency_key}"
                pubsub = r.pubsub()
                await pubsub.subscribe(channel)
                try:
                    start_wait = time.time()
                    timeout = int(os.getenv("IDEMPOTENCY_WAIT_SECONDS", "30"))
                    while time.time() - start_wait < timeout:
                        msg = await pubsub.get_message(
                            ignore_subscribe_messages=True, timeout=1.0
                        )
                        if msg and msg.get("data"):
                            try:
                                payload = (
                                    orjson.loads(msg["data"])
                                    if isinstance(msg["data"], (bytes, str))
                                    else msg["data"]
                                )
                            except Exception as e:
                                console.print(
                                    f"[bold yellow]Idempotency channel payload parse error:[/bold yellow] {e}"
                                )
                                payload = None
                            if payload:
                                return JSONResponse(status_code=208, content=payload)
                        await asyncio.sleep(0.1)
                finally:
                    try:
                        await pubsub.unsubscribe(channel)
                    except Exception as e:
                        console.print(
                            f"[bold yellow]Idempotency channel unsubscribe error:[/bold yellow] {e}"
                        )
                # Timeout waiting for master result
                raise HTTPException(
                    status_code=409,
                    detail="Idempotent request already in progress. Please retry.",
                )
        except HTTPException:
            raise
        except Exception as redis_err:
            console.print(
                f"[bold yellow]Redis idempotency read error:[/bold yellow] {redis_err}"
            )
        return None

    @staticmethod
    async def save_result(r, x_idempotency_key: str, result: dict):
        """
        Saves the finished intercept result to Redis and publishes it.
        """
        idem_key = f"idempotency:{x_idempotency_key}"
        try:
            await r.setex(
                idem_key,
                86400,
                orjson.dumps(result).decode("utf-8"),
            )
            try:
                await r.publish(
                    f"sentinel:idem:channel:{x_idempotency_key}",
                    orjson.dumps(result).decode("utf-8"),
                )
            except Exception as e:
                console.print(
                    f"[bold yellow]Redis idempotency publish error:[/bold yellow] {e}"
                )
        except Exception as redis_set_err:
            console.print(
                f"[bold yellow]Redis idempotency write error:[/bold yellow] {redis_set_err}"
            )
