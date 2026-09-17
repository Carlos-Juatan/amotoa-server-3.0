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


# ─── US5: Unified Detail Endpoint Tests ──────────────────────────────────────

@pytest.mark.asyncio
async def test_get_media_detail_returns_full_data(async_client: AsyncClient, setup_db):
    """GET /api/media/anime/10 returns full detail with user progress."""
    now = datetime.now(timezone.utc)
    await setup_db["media"].insert_one({
        "mal_id": 10,
        "type": "anime",
        "title_japanese": "鬼滅の刃",
        "title_english": "Demon Slayer",
        "title_default": "Kimetsu no Yaiba",
        "synopsis": "A boy who fights demons.",
        "cover_image_url": "http://cdn.example.com/kny.jpg",
        "gallery_image_urls": ["http://cdn.example.com/kny_1.jpg"],
        "published_status": "Finished",
        "total_units": 26,
        "season": "spring",
        "year": 2019,
        "genres": ["Action", "Fantasy"],
        "score_public": 8.7,
        "franchise_root_id": 10,
        "relations": [],
        "created_at": now,
        "updated_at": now,
    })
    await setup_db["user_progress"].insert_one({
        "account_id": "car-j-home",
        "media_mal_id": 10,
        "media_type": "anime",
        "current_unit": 12,
        "status": "watching",
        "is_favorite": True,
        "personal_tags": ["Masterpiece"],
        "external_links": [],
        "last_interacted_at": now,
    })

    response = await async_client.get(
        "/api/media/anime/10",
        headers={"X-Active-Account": "car-j-home"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mal_id"] == 10
    assert data["title_japanese"] == "鬼滅の刃"
    assert data["title_english"] == "Demon Slayer"
    assert data["synopsis"] == "A boy who fights demons."
    assert data["total_units"] == 26
    assert data["score_public"] == 8.7
    assert data["genres"] == ["Action", "Fantasy"]
    assert data["gallery_image_urls"] == ["http://cdn.example.com/kny_1.jpg"]
    assert data["user_progress"]["status"] == "watching"
    assert data["user_progress"]["current_unit"] == 12
    assert data["user_progress"]["is_favorite"] is True
    # No franchise relations for this isolated entry
    assert data["related_seasons"] == []


@pytest.mark.asyncio
async def test_get_media_detail_resolves_franchise_seasons(async_client: AsyncClient, setup_db):
    """GET /api/media/anime/20 returns related seasons resolved from franchise_root_id."""
    now = datetime.now(timezone.utc)
    # Root season (franchise_root_id points to itself → 20)
    await setup_db["media"].insert_many([
        {
            "mal_id": 20,
            "type": "anime",
            "title_japanese": "ソードアート・オンライン",
            "title_english": "Sword Art Online",
            "title_default": "Sword Art Online",
            "synopsis": "VRMMO adventure.",
            "cover_image_url": "http://cdn.example.com/sao1.jpg",
            "published_status": "Finished",
            "total_units": 25,
            "score_public": 7.2,
            "franchise_root_id": 20,
            "relations": [{"mal_id": 21, "type": "anime", "relation_type": "Sequel", "title": "SAO II"}],
            "created_at": now,
            "updated_at": now,
        },
        {
            "mal_id": 21,
            "type": "anime",
            "title_japanese": "ソードアート・オンライン II",
            "title_english": "Sword Art Online II",
            "title_default": "Sword Art Online II",
            "synopsis": "SAO II continues.",
            "cover_image_url": "http://cdn.example.com/sao2.jpg",
            "published_status": "Finished",
            "total_units": 24,
            "score_public": 6.8,
            "franchise_root_id": 20,  # Same root → unified franchise group
            "relations": [{"mal_id": 20, "type": "anime", "relation_type": "Prequel", "title": "SAO I"}],
            "created_at": now,
            "updated_at": now,
        },
    ])

    response = await async_client.get(
        "/api/media/anime/20",
        headers={"X-Active-Account": "car-j-home"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mal_id"] == 20
    # related_seasons should include the sibling (mal_id=21), not itself
    related_ids = [s["mal_id"] for s in data["related_seasons"]]
    assert 21 in related_ids
    assert 20 not in related_ids


@pytest.mark.asyncio
async def test_get_media_detail_not_found(async_client: AsyncClient, setup_db):
    """GET /api/media/anime/999 returns 404 when media does not exist."""
    response = await async_client.get(
        "/api/media/anime/999",
        headers={"X-Active-Account": "car-j-home"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_media_detail_no_progress_returns_null_progress(async_client: AsyncClient, setup_db):
    """GET /api/media/manga/30 returns null user_progress when no tracking exists."""
    now = datetime.now(timezone.utc)
    await setup_db["media"].insert_one({
        "mal_id": 30,
        "type": "manga",
        "title_japanese": "進撃の巨人",
        "title_english": "Attack on Titan",
        "title_default": "Shingeki no Kyojin",
        "cover_image_url": "http://cdn.example.com/aot.jpg",
        "published_status": "Finished",
        "total_units": 139,
        "score_public": 9.0,
        "created_at": now,
        "updated_at": now,
    })

    response = await async_client.get(
        "/api/media/manga/30",
        headers={"X-Active-Account": "car-j-home"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mal_id"] == 30
    assert data["user_progress"] is None


# ─── US2: Catalog Search, Filters, and External Import ────────────────────────

@pytest.mark.asyncio
async def test_get_media_catalog_filters(async_client: AsyncClient, setup_db):
    """GET /api/media/anime?search=Hero&genre=Action&year=2016 returns filtered results."""
    now = datetime.now(timezone.utc)
    await setup_db["media"].insert_many([
        {
            "mal_id": 40,
            "type": "anime",
            "title_japanese": "僕のヒーローアカデミア",
            "title_english": "My Hero Academia",
            "title_default": "Boku no Hero Academia",
            "cover_image_url": "http://cdn.example.com/mha.jpg",
            "published_status": "Finished",
            "total_units": 13,
            "score_public": 8.0,
            "year": 2016,
            "genres": ["Action", "Superhero"],
            "created_at": now,
            "updated_at": now,
        },
        {
            "mal_id": 41,
            "type": "anime",
            "title_japanese": "Test Anime",
            "title_default": "Test",
            "cover_image_url": "http://cdn.example.com/test.jpg",
            "published_status": "Finished",
            "total_units": 12,
            "score_public": 7.0,
            "year": 2020,
            "genres": ["Comedy"],
            "created_at": now,
            "updated_at": now,
        }
    ])

    response = await async_client.get(
        "/api/media/anime?search=Hero&genre=Action&year=2016",
        headers={"X-Active-Account": "car-j-home"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mal_id"] == 40


@pytest.mark.asyncio
async def test_search_external_media(async_client: AsyncClient, setup_db, monkeypatch):
    """GET /api/media/external/search returns mocked external results."""
    from src.services.jikan_client import JikanClient
    
    async def mock_search_anime(self, query):
        return {
            "data": [
                {
                    "mal_id": 9999,
                    "title": "Mocked External Anime",
                    "images": {"jpg": {"image_url": "http://cdn.example.com/mock.jpg"}},
                    "status": "Finished Airing",
                    "episodes": 12,
                    "year": 2025,
                    "genres": [{"name": "Sci-Fi"}],
                    "score": 9.9
                }
            ]
        }
        
    monkeypatch.setattr(JikanClient, "search_anime", mock_search_anime)

    response = await async_client.get(
        "/api/media/external/search?media_type=anime&q=Mocked",
        headers={"X-Active-Account": "car-j-home"}
    )
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mal_id"] == 9999
    assert data[0]["title_default"] == "Mocked External Anime"
    assert data[0]["year"] == 2025


@pytest.mark.asyncio
async def test_import_external_media(async_client: AsyncClient, setup_db, monkeypatch):
    """POST /api/media/external/import imports an item from Jikan to local DB."""
    from src.services.jikan_client import JikanClient
    
    async def mock_get_anime_detail(self, mal_id):
        return {
            "mal_id": mal_id,
            "title": "Imported Anime",
            "images": {"jpg": {"image_url": "http://cdn.example.com/import.jpg"}},
            "status": "Finished Airing",
            "episodes": 24,
            "year": 2021,
            "genres": [{"name": "Drama"}],
            "score": 8.5
        }
        
    monkeypatch.setattr(JikanClient, "get_anime_detail", mock_get_anime_detail)

    response = await async_client.post(
        "/api/media/external/import",
        json={"media_type": "anime", "mal_id": 8888},
        headers={"X-Active-Account": "car-j-home"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mal_id"] == 8888
    assert data["title_default"] == "Imported Anime"
    
    # Verify it is in the database
    doc = await setup_db["media"].find_one({"mal_id": 8888})
    assert doc is not None
    assert doc["title_default"] == "Imported Anime"

