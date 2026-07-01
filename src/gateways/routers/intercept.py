import os
import json
import asyncio
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from src.gateways.shared import sentinel
from src.gateways.dependencies import verify_api_key
from src.gateways.services.idempotency_srv import IdempotencyService
from src.core.logger import get_console
import redis.asyncio as redis

console = get_console()
router = APIRouter(tags=["intercept"])


@router.post("/intercept")
async def intercept_traffic(
    source: str,
    target: str,
    request: Request,
    api_key: str = Depends(verify_api_key),
    x_idempotency_key: str = Header(None),
):
    """
    HTTP Endpoint acting as the Guardian Gateway.
    Legacy agents can POST their payloads here to be scrubbed by the Immune System.
    """
    try:
        raw_body = (await request.body()).decode("utf-8")

        redis_url = os.getenv("REDIS_URL")
        r = None
        if x_idempotency_key and redis_url:
            r = redis.from_url(redis_url)
            idem_resp = await IdempotencyService.handle_idempotency(
                r, x_idempotency_key
            )
            if idem_resp is not None:
                await r.aclose()
                return idem_resp

        result = await sentinel.intercept(
            source=source, target=target, payload=raw_body
        )

        if result is None:
            if r:
                await r.aclose()
            raise HTTPException(
                status_code=400,
                detail="Payload rejected or unrecoverable by SentinelCell.",
            )

        if x_idempotency_key and r:
            await IdempotencyService.save_result(r, x_idempotency_key, result)
            await r.aclose()

        return result
    except HTTPException:
        raise
    except json.JSONDecodeError as json_err:
        console.print(f"[bold yellow]Payload Parsing Error:[/bold yellow] {json_err}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request payload format. Ensure valid JSON.",
        )
    except asyncio.TimeoutError:
        console.print("[bold red]Request Processing Timeout[/bold red]")
        raise HTTPException(
            status_code=504,
            detail="Request processing exceeded timeout. Please try again.",
        )
    except Exception as e:
        console.print(f"[bold red]Intercept Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="Payload processing failed. Check server logs for details.",
        )
