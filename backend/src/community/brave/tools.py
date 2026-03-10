"""Brave Search tool for DeerFlow."""

import json
import logging

import httpx
from langchain.tools import tool

from src.config import get_app_config

logger = logging.getLogger(__name__)

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


def _get_api_key() -> str | None:
    config = get_app_config().get_tool_config("web_search")
    if config is not None and "api_key" in config.model_extra:
        return config.model_extra.get("api_key")
    return None


@tool("web_search", parse_docstring=True)
def web_search_tool(query: str) -> str:
    """Search the web using Brave Search.

    Args:
        query: The search query.
    """
    config = get_app_config().get_tool_config("web_search")
    max_results = 5
    if config is not None and "max_results" in config.model_extra:
        max_results = int(config.model_extra.get("max_results", 5))

    api_key = _get_api_key()
    if not api_key:
        return json.dumps({"error": "BRAVE_API_KEY not configured"})

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": max_results,
        "search_lang": "en",
        "safesearch": "moderate",
        "freshness": "pm",
    }

    try:
        response = httpx.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        results = []
        for r in data.get("web", {}).get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("description", ""),
            })

        return json.dumps(results, indent=2, ensure_ascii=False)

    except Exception as exc:
        logger.exception("Brave search failed: %s", exc)
        return json.dumps({"error": str(exc)})
