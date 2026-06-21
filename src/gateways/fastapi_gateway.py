from fastapi import FastAPI, Request, HTTPException
from src.agents.validator_agent import SentinelCell

app = FastAPI(
    title="SentinelCell Guardian Gateway",
    description="Transparent API Gateway for Multi-Agent Systems",
)
sentinel = SentinelCell()


@app.post("/intercept")
async def intercept_traffic(source: str, target: str, request: Request):
    """
    HTTP Endpoint acting as the Guardian Gateway.
    Legacy agents can POST their payloads here to be scrubbed by the Immune System.
    """
    try:
        raw_body = (await request.body()).decode("utf-8")
        result = await sentinel.intercept(
            source=source, target=target, payload=raw_body
        )

        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Payload rejected or unrecoverable by SentinelCell.",
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
