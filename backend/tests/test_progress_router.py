"""
T030: Tests for User Story 6 — Progress, Tags, Links, and Franchise Movies endpoints.
"""
import pytest
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ACCOUNT = "car-j-home"
HEADERS = {"X-Active-Account": ACCOUNT}
NOW = datetime.now(timezone.utc).isoformat()

ANIME_DOC = {
    "mal_id": 1001,
    "type": "anime",
    "title_japanese": "テスト アニメ",
    "title_english": "Test Anime",
    "title_default": "Test Anime",
    "cover_image_url": "https://cdn.example.com/test.jpg",
    "published_status": "Currently Airing",
    "total_units": 24,
    "created_at": NOW,
    "updated_at": NOW,
}

MANGA_DOC = {
    "mal_id": 2001,
    "type": "manga",
    "title_japanese": "テスト マンガ",
    "title_english": "Test Manga",
    "title_default": "Test Manga",
    "cover_image_url": "https://cdn.example.com/manga.jpg",
    "published_status": "Publishing",
    "total_units": 120,
    "created_at": NOW,
    "updated_at": NOW,
}

PROGRESS_DOC = {
    "account_id": ACCOUNT,
    "media_mal_id": 1001,
    "media_type": "anime",
    "current_unit": 5,
    "status": "watching",
    "is_favorite": False,
    "personal_score": None,
    "personal_tags": [],
    "external_links": [],
    "franchise_movies": [],
    "last_interacted_at": NOW,
    "completed_at": None,
}


# ---------------------------------------------------------------------------
# T030: Progress update endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_progress_creates_new_record(async_client, setup_db):
    """PUT /api/media/anime/1001/progress creates a new progress record when none exists."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())

    resp = await async_client.put(
        "/api/media/anime/1001/progress",
        headers=HEADERS,
        json={"current_unit": 3, "status": "watching", "is_favorite": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_unit"] == 3
    assert body["status"] == "watching"
    assert body["account_id"] == ACCOUNT
    assert body["media_mal_id"] == 1001


@pytest.mark.asyncio
async def test_update_progress_updates_existing_record(async_client, setup_db):
    """PUT /api/media/anime/1001/progress updates existing progress document."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())
    await setup_db["user_progress"].insert_one(PROGRESS_DOC.copy())

    resp = await async_client.put(
        "/api/media/anime/1001/progress",
        headers=HEADERS,
        json={"current_unit": 10, "status": "watching", "personal_score": 9},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_unit"] == 10
    assert body["personal_score"] == 9


@pytest.mark.asyncio
async def test_update_progress_marks_completed_when_unit_reaches_total(async_client, setup_db):
    """PUT /api/media/anime/1001/progress auto-completes when current_unit == total_units."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())

    resp = await async_client.put(
        "/api/media/anime/1001/progress",
        headers=HEADERS,
        json={"current_unit": 24, "status": "watching"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"


@pytest.mark.asyncio
async def test_update_progress_rejects_unit_exceeding_total(async_client, setup_db):
    """PUT /api/media/anime/1001/progress returns 422 when current_unit exceeds total_units."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())

    resp = await async_client.put(
        "/api/media/anime/1001/progress",
        headers=HEADERS,
        json={"current_unit": 99, "status": "watching"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_progress_404_for_missing_media(async_client, setup_db):
    """PUT /api/media/anime/9999/progress returns 404 if media item not found."""
    resp = await async_client.put(
        "/api/media/anime/9999/progress",
        headers=HEADERS,
        json={"current_unit": 1, "status": "watching"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# T030: External Links endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_links(async_client, setup_db):
    """PUT /api/media/anime/1001/links replaces external links for an account."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())
    await setup_db["user_progress"].insert_one(PROGRESS_DOC.copy())

    new_links = [
        {"label": "Crunchyroll", "url": "https://crunchyroll.com/series/test"},
        {"label": "HiDive", "url": "https://hidive.com/test"},
    ]
    resp = await async_client.put(
        "/api/media/anime/1001/links",
        headers=HEADERS,
        json=new_links,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["external_links"]) == 2
    assert body["external_links"][0]["label"] == "Crunchyroll"


@pytest.mark.asyncio
async def test_update_links_creates_progress_if_missing(async_client, setup_db):
    """PUT /api/media/anime/1001/links creates progress record if none exists yet."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())

    resp = await async_client.put(
        "/api/media/anime/1001/links",
        headers=HEADERS,
        json=[{"label": "Netflix", "url": "https://netflix.com/test"}],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["external_links"][0]["label"] == "Netflix"


# ---------------------------------------------------------------------------
# T030: Tags endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_tags(async_client, setup_db):
    """PUT /api/media/anime/1001/tags replaces personal tags."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())
    await setup_db["user_progress"].insert_one(PROGRESS_DOC.copy())

    resp = await async_client.put(
        "/api/media/anime/1001/tags",
        headers=HEADERS,
        json={"tags": ["Masterpiece", "Rever"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "Masterpiece" in body["personal_tags"]
    assert "Rever" in body["personal_tags"]


@pytest.mark.asyncio
async def test_update_tags_creates_progress_if_missing(async_client, setup_db):
    """PUT /api/media/anime/1001/tags creates progress record if none exists."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())

    resp = await async_client.put(
        "/api/media/anime/1001/tags",
        headers=HEADERS,
        json={"tags": ["Favorito"]},
    )
    assert resp.status_code == 200
    assert "Favorito" in resp.json()["personal_tags"]


# ---------------------------------------------------------------------------
# T030: Franchise Movies endpoints (anime-only)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_franchise_movie(async_client, setup_db):
    """POST /api/media/anime/1001/movies adds a movie to the franchise list."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())
    await setup_db["user_progress"].insert_one(PROGRESS_DOC.copy())

    movie_payload = {
        "title": "Kimetsu no Yaiba: Mugen Train",
        "cover_image_url": "https://cdn.example.com/movie.jpg",
        "release_year": 2020,
    }
    resp = await async_client.post(
        "/api/media/anime/1001/movies",
        headers=HEADERS,
        json=movie_payload,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["franchise_movies"][0]["title"] == "Kimetsu no Yaiba: Mugen Train"
    assert body["franchise_movies"][0]["watched"] is False
    assert "movie_id" in body["franchise_movies"][0]


@pytest.mark.asyncio
async def test_add_franchise_movie_rejected_for_manga(async_client, setup_db):
    """POST /api/media/manga/2001/movies is rejected (403) for non-anime media."""
    await setup_db["media"].insert_one(MANGA_DOC.copy())

    resp = await async_client.post(
        "/api/media/manga/2001/movies",
        headers=HEADERS,
        json={"title": "Invalid Movie"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_toggle_franchise_movie_watched(async_client, setup_db):
    """PATCH /api/media/anime/1001/movies/{movie_id} toggles a movie's watched status."""
    import uuid

    movie_id = str(uuid.uuid4())
    progress_with_movie = {
        **PROGRESS_DOC,
        "franchise_movies": [
            {
                "movie_id": movie_id,
                "title": "Test Movie",
                "cover_image_url": None,
                "watched": False,
                "release_year": 2021,
            }
        ],
    }
    await setup_db["media"].insert_one(ANIME_DOC.copy())
    await setup_db["user_progress"].insert_one(progress_with_movie)

    resp = await async_client.patch(
        f"/api/media/anime/1001/movies/{movie_id}",
        headers=HEADERS,
        json={"watched": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["franchise_movies"][0]["watched"] is True


@pytest.mark.asyncio
async def test_toggle_movie_404_for_unknown_movie_id(async_client, setup_db):
    """PATCH /api/media/anime/1001/movies/{movie_id} returns 404 for unknown movie_id."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())
    await setup_db["user_progress"].insert_one(PROGRESS_DOC.copy())

    resp = await async_client.patch(
        "/api/media/anime/1001/movies/nonexistent-id",
        headers=HEADERS,
        json={"watched": True},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# US7: Active Progress & Increment Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_active_progress_returns_active_media(async_client, setup_db):
    """GET /api/media/anime/active-progress returns only Currently Airing media with progress."""
    # Active anime
    active_anime = ANIME_DOC.copy()
    active_anime["published_status"] = "Currently Airing"
    
    # Finished anime
    finished_anime = ANIME_DOC.copy()
    finished_anime["mal_id"] = 1002
    finished_anime["published_status"] = "Finished Airing"
    
    await setup_db["media"].insert_many([active_anime, finished_anime])
    
    progress_active = PROGRESS_DOC.copy()
    progress_active["media_mal_id"] = 1001
    
    progress_finished = PROGRESS_DOC.copy()
    progress_finished["media_mal_id"] = 1002
    progress_finished["_id"] = "222222222222222222222222"
    
    await setup_db["user_progress"].insert_many([progress_active, progress_finished])
    
    resp = await async_client.get(
        "/api/media/anime/active-progress",
        headers=HEADERS,
    )
    if resp.status_code != 200:
        print("ERROR:", resp.text)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["mal_id"] == 1001
    assert body[0]["user_progress"]["current_unit"] == 5


@pytest.mark.asyncio
async def test_increment_progress(async_client, setup_db):
    """POST /api/media/anime/1001/increment increases unit by 1."""
    await setup_db["media"].insert_one(ANIME_DOC.copy())
    await setup_db["user_progress"].insert_one(PROGRESS_DOC.copy())  # currently at 12

    resp = await async_client.post(
        "/api/media/anime/1001/increment",
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_unit"] == 6


@pytest.mark.asyncio
async def test_increment_progress_marks_completed(async_client, setup_db):
    """POST /api/media/anime/1001/increment marks as completed if new unit == total_units."""
    await setup_db["media"].insert_one(ANIME_DOC.copy()) # total 24
    
    prog = PROGRESS_DOC.copy()
    prog["current_unit"] = 23
    await setup_db["user_progress"].insert_one(prog)

    resp = await async_client.post(
        "/api/media/anime/1001/increment",
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_unit"] == 24
    assert body["status"] == "completed"
