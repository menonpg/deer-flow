"""
Reverse proxy: forwards /api/langgraph/* → http://localhost:2024/*

The LangGraph dev server runs on port 2024 inside the same container. Railway
only exposes one public port (8001 / gateway), so we proxy LangGraph through
the gateway. This keeps the frontend pointed at a single backend origin.
"""

import logging

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

LANGGRAPH_BASE = "http://localhost:2024"

router = APIRouter()


@router.api_route(
    "/api/langgraph/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def langgraph_proxy(path: str, request: Request) -> Response:
    """Proxy all /api/langgraph/* requests to the LangGraph server on :2024."""

    target_url = f"{LANGGRAPH_BASE}/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    headers = dict(request.headers)
    # Strip hop-by-hop headers
    for h in ("host", "connection", "transfer-encoding", "content-length"):
        headers.pop(h, None)

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            upstream = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

        # Stream back the response
        resp_headers = dict(upstream.headers)
        for h in ("transfer-encoding", "connection"):
            resp_headers.pop(h, None)

        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=resp_headers,
            media_type=upstream.headers.get("content-type"),
        )

    except httpx.ConnectError:
        logger.warning("LangGraph server not reachable at %s", LANGGRAPH_BASE)
        return Response(
            content=b'{"detail":"LangGraph server not ready yet — please retry in a few seconds"}',
            status_code=503,
            media_type="application/json",
        )
    except Exception as exc:
        logger.exception("Proxy error forwarding to LangGraph: %s", exc)
        return Response(
            content=b'{"detail":"Proxy error"}',
            status_code=502,
            media_type="application/json",
        )
