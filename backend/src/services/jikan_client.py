"""
JikanClient: Rate-limited async HTTP client for Jikan API v4.

Strategy:
- Token Bucket: capped at 2 tokens/second (safe headroom below Jikan's 3 req/s limit).
- Exponential backoff with jitter for HTTP 429, 502, 503, 504 and transient network errors.
- Respects `Retry-After` header on HTTP 429.
- Up to MAX_RETRIES (5) retry attempts before raising.
"""

import asyncio
import logging
import random
import time
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JIKAN_BASE_URL = "https://api.jikan.moe/v4"

# Token bucket configuration
TOKEN_BUCKET_CAPACITY = 2       # max burst size (tokens)
TOKEN_REFILL_RATE = 2.0         # tokens replenished per second

# Retry configuration
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 3.0      # base wait on first retry
MAX_BACKOFF_SECONDS = 60.0      # upper cap for backoff
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


# ---------------------------------------------------------------------------
# Token Bucket
# ---------------------------------------------------------------------------

class TokenBucket:
    """
    A thread-safe (asyncio) token bucket for rate limiting.

    Tokens refill continuously at `refill_rate` per second up to `capacity`.
    Each request consumes one token; if none available, `acquire()` sleeps
    until a token is available.
    """

    def __init__(self, capacity: float = TOKEN_BUCKET_CAPACITY, refill_rate: float = TOKEN_REFILL_RATE) -> None:
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = float(capacity)
        self._last_refill: float = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Compute new tokens based on elapsed time (called under lock)."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
        self._last_refill = now

    async def acquire(self) -> None:
        """Block until one token is available, then consume it."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                # Calculate how long until one token is ready
                wait_time = (1.0 - self._tokens) / self._refill_rate
            await asyncio.sleep(wait_time)


# ---------------------------------------------------------------------------
# JikanClient
# ---------------------------------------------------------------------------

class JikanClient:
    """
    Async HTTP client for Jikan API v4 with:
    - Token bucket rate limiting (2 req/s)
    - Exponential backoff retry for transient errors
    - Proper resource lifecycle management (use as async context manager)
    """

    def __init__(
        self,
        base_url: str = JIKAN_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._bucket = TokenBucket()
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "JikanClient":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={"Accept": "application/json"},
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Internal request dispatcher
    # ------------------------------------------------------------------

    async def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Dispatch an HTTP request through the token bucket and retry policy.

        Raises:
            httpx.HTTPStatusError: When all retries are exhausted.
            RuntimeError: When called outside the async context manager.
        """
        if self._client is None:
            raise RuntimeError("JikanClient must be used as an async context manager.")

        last_exc: Optional[Exception] = None
        for attempt in range(MAX_RETRIES + 1):
            # Acquire a rate-limit token before sending the request
            await self._bucket.acquire()
            try:
                response = await self._client.request(method, path, **kwargs)

                if response.status_code not in RETRYABLE_STATUS_CODES:
                    response.raise_for_status()
                    return response.json()

                # Handle retryable status codes
                retry_after: Optional[str] = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait = float(retry_after)
                    except ValueError:
                        wait = BASE_BACKOFF_SECONDS
                else:
                    # Exponential backoff with jitter
                    wait = min(
                        BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0.0, 1.0),
                        MAX_BACKOFF_SECONDS,
                    )

                logger.warning(
                    "Jikan API returned %d on %s %s (attempt %d/%d). Retrying in %.1fs...",
                    response.status_code,
                    method.upper(),
                    path,
                    attempt + 1,
                    MAX_RETRIES,
                    wait,
                )
                last_exc = httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
                await asyncio.sleep(wait)

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                wait = min(
                    BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0.0, 1.0),
                    MAX_BACKOFF_SECONDS,
                )
                logger.warning(
                    "Network error on %s %s (attempt %d/%d): %s. Retrying in %.1fs...",
                    method.upper(),
                    path,
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                    wait,
                )
                last_exc = exc
                await asyncio.sleep(wait)

        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def get_seasonal_anime(self, year: int, season: str) -> List[Dict[str, Any]]:
        """
        Fetch all anime for a given year and season via paginated Jikan endpoint.

        Args:
            year: e.g. 2024
            season: one of "winter", "spring", "summer", "fall"

        Returns:
            List of raw Jikan anime data objects.
        """
        results: List[Dict[str, Any]] = []
        page = 1
        while True:
            path = f"/seasons/{year}/{season}"
            data = await self._request("GET", path, params={"page": page})
            page_items: List[Dict[str, Any]] = data.get("data", [])
            results.extend(page_items)

            pagination = data.get("pagination", {})
            has_next = pagination.get("has_next_page", False)
            if not has_next:
                break
            page += 1

        return results

    async def get_anime_detail(self, mal_id: int) -> Dict[str, Any]:
        """Fetch full anime metadata including relations from Jikan."""
        data = await self._request("GET", f"/anime/{mal_id}/full")
        return data.get("data", {})

    async def get_manga_detail(self, mal_id: int) -> Dict[str, Any]:
        """Fetch full manga/light novel metadata including relations from Jikan."""
        data = await self._request("GET", f"/manga/{mal_id}/full")
        return data.get("data", {})

    async def search_anime(self, query: str, page: int = 1) -> Dict[str, Any]:
        """Search anime by title query."""
        data = await self._request(
            "GET",
            "/anime",
            params={"q": query, "page": page, "limit": 25},
        )
        return data

    async def search_manga(self, query: str, page: int = 1) -> Dict[str, Any]:
        """Search manga/light novel by title query."""
        data = await self._request(
            "GET",
            "/manga",
            params={"q": query, "page": page, "limit": 25},
        )
        return data

    async def get_current_season(self) -> Dict[str, Any]:
        """Fetch the currently airing anime season."""
        data = await self._request("GET", "/seasons/now")
        return data

    async def get_manga_publishing(self, page: int = 1) -> Dict[str, Any]:
        """
        Fetch currently publishing manga/light novels paginated.
        Uses status=publishing filter.
        """
        data = await self._request(
            "GET",
            "/manga",
            params={"status": "publishing", "page": page, "limit": 25, "order_by": "mal_id"},
        )
        return data
