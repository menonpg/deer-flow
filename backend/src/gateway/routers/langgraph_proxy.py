"""
Reverse proxy: forwards /api/langgraph/* → http://localhost:2024/*

The LangGraph dev server runs on port 2024 inside the same container. Railway
only exposes one public port (8001 / gateway), so we proxy LangGraph through
the gateway. This keeps the frontend pointed at a single backend origin.

IMPORTANT: SSE (text/event-stream) responses are streamed chunk-by-chunk so
the browser receives events in real-time. Non-streaming responses are buffered
normally. Using the buffered path for SSE would hold the entire agent run in
memory before delivering anything — producing the "thinking spinner forever
then instant dump" symptom.
"""

import logging
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

LANGGRAPH_BASE = "http://localhost:2024"

# httpx client reused across requests (connection pool)
_client = httpx.AsyncClient(timeout=None)  # no timeout — long agent runs

router = APIRouter()


def _strip_hop_by_hop(headers: dict) -> dict:
    drop = {"host", "connection", "transfer-encoding", "content-length",
            "keep-alive", "proxy-authenticate", "proxy-authorization",
            "te", "trailers", "upgrade"}
    return {k: v for k, v in headers.items() if k.lower() not in drop}


async def _stream_chunks(response: httpx.Response) -> AsyncIterator[bytes]:
    """Yield raw bytes from the upstream SSE response as they arrive."""
    async for chunk in response.aiter_raw():
        if chunk:
            yield chunk


@router.api_route(
    "/api/langgraph/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def langgraph_proxy(path: str, request: Request) -> Response:
    """Proxy all /api/langgraph/* requests to the LangGraph server on :2024."""

    target_url = f"{LANGGRAPH_BASE}/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    req_headers = _strip_hop_by_hop(dict(request.headers))
    body = await request.body()

    try:
        # Open a streaming request — don't await the full response body yet
        upstream_req = _client.build_request(
            method=request.method,
            url=target_url,
            headers=req_headers,
            content=body,
        )
        upstream = await _client.send(upstream_req, stream=True)

        resp_headers = _strip_hop_by_hop(dict(upstream.headers))
        content_type = upstream.headers.get("content-type", "")

        if "text/event-stream" in content_type:
            # True streaming: forward each SSE chunk immediately as it arrives
            return StreamingResponse(
                _stream_chunks(upstream),
                status_code=upstream.status_code,
                headers=resp_headers,
                media_type="text/event-stream",
            )

        # Non-streaming: buffer and return normally
        content = await upstream.aread()
        await upstream.aclose()
        return Response(
            content=content,
            status_code=upstream.status_code,
            headers=resp_headers,
            media_type=content_type or None,
        )

    except httpx.ConnectError:
        logger.warning("LangGraph server not reachable at %s", LANGGRAPH_BASE)
        return Response(
            content=b'{"detail":"LangGraph server not ready yet - please retry in a few seconds"}',
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
