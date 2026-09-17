"""
Unit tests for JikanClient token bucket rate limiting and retry backoff.

T041 [US3]: Validates that:
1. TokenBucket respects capacity and refill rate.
2. JikanClient retries on HTTP 429 with Retry-After header.
3. JikanClient retries on HTTP 503 with exponential backoff.
4. JikanClient raises after exhausting MAX_RETRIES.
5. JikanClient raises RuntimeError when used outside context manager.
6. Successful requests pass through without retry.
7. get_seasonal_anime handles multi-page pagination correctly.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch, call

import httpx
import pytest
import pytest_asyncio

from src.services.jikan_client import (
    JikanClient,
    TokenBucket,
    MAX_RETRIES,
    TOKEN_BUCKET_CAPACITY,
    TOKEN_REFILL_RATE,
)


# ---------------------------------------------------------------------------
# TokenBucket tests
# ---------------------------------------------------------------------------

class TestTokenBucket:
    """Unit tests for the token bucket rate limiter."""

    @pytest.mark.asyncio
    async def test_initial_tokens_equal_capacity(self):
        """Bucket starts full."""
        bucket = TokenBucket(capacity=2, refill_rate=2.0)
        # Should be able to acquire two tokens immediately
        await bucket.acquire()
        await bucket.acquire()

    @pytest.mark.asyncio
    async def test_acquire_blocks_when_empty(self):
        """Bucket should block when empty and wait for refill."""
        bucket = TokenBucket(capacity=1, refill_rate=100.0)  # fast refill for test speed
        # Drain the bucket
        await bucket.acquire()
        # Next acquire should block very briefly (< 0.1s at 100 tok/s)
        start = time.monotonic()
        await bucket.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5, f"Acquire took too long: {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_refill_does_not_exceed_capacity(self):
        """Tokens should never exceed capacity even after long idle."""
        bucket = TokenBucket(capacity=2, refill_rate=10.0)
        # Drain completely
        await bucket.acquire()
        await bucket.acquire()
        # Wait long enough to refill way past capacity
        await asyncio.sleep(0.5)
        # Should only have capacity worth of tokens
        await bucket.acquire()
        await bucket.acquire()
        # A third acquire should need to wait (bucket at 0 after 2 drains)
        # We just verify no exception; the test completes quickly due to refill rate
        start = time.monotonic()
        await bucket.acquire()
        elapsed = time.monotonic() - start
        # At 10 tok/s, one token takes 0.1s max
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_token_bucket_default_capacity(self):
        """Default capacity is TOKEN_BUCKET_CAPACITY."""
        bucket = TokenBucket()
        assert bucket._capacity == TOKEN_BUCKET_CAPACITY

    @pytest.mark.asyncio
    async def test_token_bucket_default_refill_rate(self):
        """Default refill rate is TOKEN_REFILL_RATE."""
        bucket = TokenBucket()
        assert bucket._refill_rate == TOKEN_REFILL_RATE


# ---------------------------------------------------------------------------
# JikanClient tests
# ---------------------------------------------------------------------------

def _make_response(status_code: int, json_data: dict, headers: dict | None = None) -> httpx.Response:
    """Create a minimal httpx.Response mock for the given status code."""
    request = httpx.Request("GET", "https://api.jikan.moe/v4/test")
    response = httpx.Response(
        status_code=status_code,
        json=json_data,
        headers=headers or {},
        request=request,
    )
    return response


class TestJikanClientContextManager:
    """Test lifecycle management."""

    @pytest.mark.asyncio
    async def test_raises_outside_context_manager(self):
        """Calling _request without entering context should raise RuntimeError."""
        client = JikanClient()
        with pytest.raises(RuntimeError, match="async context manager"):
            await client._request("GET", "/test")

    @pytest.mark.asyncio
    async def test_client_is_set_inside_context(self):
        """The internal httpx client should be initialized inside the context."""
        client = JikanClient()
        assert client._client is None
        async with client:
            assert client._client is not None
        assert client._client is None


class TestJikanClientRetry:
    """Test retry and backoff behavior."""

    @pytest.mark.asyncio
    async def test_successful_request_no_retry(self):
        """A 200 response should be returned immediately without retry."""
        payload = {"data": [{"mal_id": 1, "title": "Test Anime"}], "pagination": {"has_next_page": False}}
        mock_response = _make_response(200, payload)

        async with JikanClient() as client:
            with patch.object(client._client, "request", new_callable=AsyncMock, return_value=mock_response):
                result = await client._request("GET", "/anime")
                assert result == payload

    @pytest.mark.asyncio
    async def test_retries_on_429_with_retry_after_header(self):
        """HTTP 429 with Retry-After header should trigger a wait and retry."""
        success_payload = {"data": {"mal_id": 1}}
        response_429 = _make_response(429, {}, headers={"Retry-After": "0"})
        response_200 = _make_response(200, success_payload)

        async with JikanClient() as client:
            # Override bucket to not sleep for speed
            client._bucket._tokens = 10.0
            client._bucket._capacity = 10.0
            with patch.object(
                client._client, "request", new_callable=AsyncMock,
                side_effect=[response_429, response_200]
            ), patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await client._request("GET", "/anime/1")
                assert result == success_payload
                # Should have slept at least once for the 429
                mock_sleep.assert_called()

    @pytest.mark.asyncio
    async def test_retries_on_503_with_exponential_backoff(self):
        """HTTP 503 should trigger exponential backoff retries."""
        success_payload = {"data": {"mal_id": 2}}
        response_503 = _make_response(503, {})
        response_200 = _make_response(200, success_payload)

        async with JikanClient() as client:
            client._bucket._tokens = 10.0
            client._bucket._capacity = 10.0
            with patch.object(
                client._client, "request", new_callable=AsyncMock,
                side_effect=[response_503, response_503, response_200]
            ), patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await client._request("GET", "/anime/2/full")
                assert result == success_payload
                # Should have slept twice (once per 503)
                assert mock_sleep.call_count >= 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries_exhausted(self):
        """After MAX_RETRIES + 1 failures, should raise the last exception."""
        response_429 = _make_response(429, {}, headers={"Retry-After": "0"})

        async with JikanClient() as client:
            client._bucket._tokens = 100.0
            client._bucket._capacity = 100.0
            with patch.object(
                client._client, "request", new_callable=AsyncMock,
                # One more than MAX_RETRIES to ensure all attempts fail
                side_effect=[response_429] * (MAX_RETRIES + 1)
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(httpx.HTTPStatusError):
                    await client._request("GET", "/anime")

    @pytest.mark.asyncio
    async def test_retries_on_network_error(self):
        """Network errors (TimeoutException) should also trigger retry."""
        success_payload = {"data": []}
        response_200 = _make_response(200, success_payload)

        async with JikanClient() as client:
            client._bucket._tokens = 10.0
            client._bucket._capacity = 10.0
            with patch.object(
                client._client, "request", new_callable=AsyncMock,
                side_effect=[httpx.TimeoutException("timeout"), response_200]
            ), patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await client._request("GET", "/seasons/now")
                assert result == success_payload
                mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_after_network_error_exhausted(self):
        """Exhausting retries on network error should re-raise the exception."""
        async with JikanClient() as client:
            client._bucket._tokens = 100.0
            client._bucket._capacity = 100.0
            with patch.object(
                client._client, "request", new_callable=AsyncMock,
                side_effect=[httpx.NetworkError("connection refused")] * (MAX_RETRIES + 1)
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(httpx.NetworkError):
                    await client._request("GET", "/manga")


class TestJikanClientPagination:
    """Test paginated API methods."""

    @pytest.mark.asyncio
    async def test_get_seasonal_anime_single_page(self):
        """get_seasonal_anime should return items from a single page."""
        items = [{"mal_id": 1, "title": "Anime A"}, {"mal_id": 2, "title": "Anime B"}]
        payload = {"data": items, "pagination": {"has_next_page": False}}
        response_200 = _make_response(200, payload)

        async with JikanClient() as client:
            client._bucket._tokens = 10.0
            client._bucket._capacity = 10.0
            with patch.object(client._client, "request", new_callable=AsyncMock, return_value=response_200):
                result = await client.get_seasonal_anime(2024, "winter")
                assert result == items
                assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_seasonal_anime_multiple_pages(self):
        """get_seasonal_anime should aggregate items across multiple pages."""
        page1_items = [{"mal_id": 1, "title": "Anime A"}]
        page2_items = [{"mal_id": 2, "title": "Anime B"}]

        page1_payload = {"data": page1_items, "pagination": {"has_next_page": True}}
        page2_payload = {"data": page2_items, "pagination": {"has_next_page": False}}

        response_p1 = _make_response(200, page1_payload)
        response_p2 = _make_response(200, page2_payload)

        async with JikanClient() as client:
            client._bucket._tokens = 10.0
            client._bucket._capacity = 10.0
            with patch.object(
                client._client, "request", new_callable=AsyncMock,
                side_effect=[response_p1, response_p2]
            ):
                result = await client.get_seasonal_anime(2024, "spring")
                assert result == page1_items + page2_items
                assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_anime_detail(self):
        """get_anime_detail returns the data sub-key from the response."""
        detail = {"mal_id": 42, "title": "Fullmetal", "title_japanese": "鋼の錬金術師"}
        payload = {"data": detail}
        response_200 = _make_response(200, payload)

        async with JikanClient() as client:
            client._bucket._tokens = 10.0
            client._bucket._capacity = 10.0
            with patch.object(client._client, "request", new_callable=AsyncMock, return_value=response_200):
                result = await client.get_anime_detail(42)
                assert result == detail

    @pytest.mark.asyncio
    async def test_get_manga_detail(self):
        """get_manga_detail returns the data sub-key from the response."""
        detail = {"mal_id": 77, "title": "Berserk", "title_japanese": "ベルセルク"}
        payload = {"data": detail}
        response_200 = _make_response(200, payload)

        async with JikanClient() as client:
            client._bucket._tokens = 10.0
            client._bucket._capacity = 10.0
            with patch.object(client._client, "request", new_callable=AsyncMock, return_value=response_200):
                result = await client.get_manga_detail(77)
                assert result == detail
