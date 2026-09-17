import pytest
from httpx import AsyncClient
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_get_media_anime_showcase(async_client: AsyncClient, setup_db):
    # Seed mock data
    await setup_db["media"].insert_one({
        "mal_id": 1,
        "type": "anime",
        "title_japanese": "Test Anime",
        "title_default": "Test Anime Default",
        "cover_image_url": "http://test.jpg",
        "published_status": "Finished",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })
    await setup_db["user_progress"].insert_one({
        "account_id": "car-j-home",
        "media_mal_id": 1,
        "media_type": "anime",
        "current_unit": 1,
        "status": "watching",
        "is_favorite": True,
        "personal_tags": [],
        "external_links": [],
        "last_interacted_at": datetime.now(timezone.utc)
    })

    # Request the anime endpoint
    response = await async_client.get("/api/media/anime", headers={"X-Active-Account": "car-j-home"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mal_id"] == 1
    assert data[0]["title_japanese"] == "Test Anime"
    assert data[0]["user_progress"]["status"] == "watching"
