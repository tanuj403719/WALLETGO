"""
Shared async httpx client for inter-service communication.
Includes retry logic with exponential backoff for transient failures.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

logger = logging.getLogger("prism.gateway.client")

# Populated by the lifespan context manager in main.py
_client: Optional[httpx.AsyncClient] = None

_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 0.5  # seconds; doubles each attempt


def get_client() -> httpx.AsyncClient:
    assert _client is not None, "httpx client not initialised — check lifespan"
    return _client


async def forward(
    method: str,
    url: str,
    *,
    json: Any = None,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Forward a request to a downstream service and return the parsed JSON.

    Retries up to _MAX_RETRIES times on connection errors and 5xx responses,
    with exponential backoff.  Raises HTTPException on final failure.
    """
    client = get_client()
    last_exc: Optional[Exception] = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = await client.request(method, url, json=json, params=params)
            response.raise_for_status()
            return response.json()

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    "Attempt %d/%d failed for %s (%s). Retrying in %.1fs…",
                    attempt, _MAX_RETRIES, url, type(exc).__name__, wait,
                )
                await asyncio.sleep(wait)
            else:
                logger.error("All %d attempts failed for %s: %s", _MAX_RETRIES, url, exc)

        except httpx.HTTPStatusError as exc:
            # Don't retry client errors (4xx); only retry server errors (5xx)
            if exc.response.status_code < 500:
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=exc.response.text,
                )
            last_exc = exc
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    "Attempt %d/%d got %d from %s. Retrying in %.1fs…",
                    attempt, _MAX_RETRIES, exc.response.status_code, url, wait,
                )
                await asyncio.sleep(wait)
            else:
                logger.error("All %d attempts failed for %s: %s", _MAX_RETRIES, url, exc)
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=exc.response.text,
                )

    # Connection / timeout exhausted
    if isinstance(last_exc, httpx.TimeoutException):
        raise HTTPException(status_code=504, detail=f"Downstream service timed out: {url}")
    raise HTTPException(status_code=503, detail=f"Downstream service unavailable: {url}")
