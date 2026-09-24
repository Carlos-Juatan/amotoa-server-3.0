"""
T052: Unit and integration tests for BatchWorker lifecycle and resume.

Covers:
- Job creation and initial state
- Anime season chunking (year × season iteration)
- Manga/LN page chunking
- Pause/resume: worker checks status flag in DB and exits cleanly
- Discrete error logging: a single failed item does not crash the batch
- Cursor persistence: job is updated after each chunk
- Import skip policy: existing mal_ids are not re-imported
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

from src.services.batch_worker import BatchWorker
from src.services.media_service import MediaService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jikan_anime(mal_id: int, title: str = "Test Anime") -> Dict[str, Any]:
    return {
        "mal_id": mal_id,
        "title": title,
        "title_japanese": f"{title}JP",
        "title_english": title,
        "status": "Finished Airing",
        "season": "winter",
        "year": 2020,
        "score": 7.5,
        "episodes": 12,
        "genres": [],
        "themes": [],
        "images": {
            "jpg": {"large_image_url": f"https://cdn.test/{mal_id}.jpg"},
            "webp": {},
        },
        "relations": [],
    }


def _make_jikan_manga(mal_id: int, title: str = "Test Manga") -> Dict[str, Any]:
    return {
        "mal_id": mal_id,
        "title": title,
        "title_japanese": f"{title}JP",
        "title_english": title,
        "status": "Publishing",
        "score": 8.0,
        "chapters": None,
        "genres": [],
        "themes": [],
        "images": {
            "jpg": {"large_image_url": f"https://cdn.test/{mal_id}.jpg"},
            "webp": {},
        },
        "relations": [],
    }


@pytest_asyncio.fixture()
async def mock_db():
    """Isolated in-memory MongoDB per test."""
    client = AsyncMongoMockClient()
    db = client.get_database(f"test_batch_{uuid.uuid4().hex}")
    yield db
    await client.drop_database(db.name)


@pytest_asyncio.fixture()
async def worker(mock_db):
    return BatchWorker(db=mock_db)


# ---------------------------------------------------------------------------
# T052-A: Job creation — initial document persisted correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_job_persists_to_db(worker, mock_db):
    job = await worker.create_job(
        media_type="anime",
        year_start=2020,
        year_end=2020,
    )
    assert job["status"] == "pending"
    assert job["media_type"] == "anime"
    assert job["year_start"] == 2020
    assert job["year_end"] == 2020
    assert "job_id" in job
    assert job["progress"]["imported"] == 0

    # Verify persisted in DB
    from_db = await mock_db["batch_import_jobs"].find_one({"job_id": job["job_id"]})
    assert from_db is not None
    assert from_db["status"] == "pending"


# ---------------------------------------------------------------------------
# T052-B: Anime batch — seasons iterated in order, items imported
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_anime_batch_imports_single_season(worker, mock_db):
    # Each season returns TWO DIFFERENT mal_ids unique to that season so none are skipped
    season_items = {
        "winter": [_make_jikan_anime(1101, "Winter A"), _make_jikan_anime(1102, "Winter B")],
        "spring": [_make_jikan_anime(1201, "Spring A"), _make_jikan_anime(1202, "Spring B")],
        "summer": [_make_jikan_anime(1301, "Summer A"), _make_jikan_anime(1302, "Summer B")],
        "fall":   [_make_jikan_anime(1401, "Fall A"),   _make_jikan_anime(1402, "Fall B")],
    }

    async def side_effect(year, season):
        return season_items[season]

    mock_jikan = AsyncMock()
    mock_jikan.__aenter__ = AsyncMock(return_value=mock_jikan)
    mock_jikan.__aexit__ = AsyncMock(return_value=False)
    mock_jikan.get_seasonal_anime = AsyncMock(side_effect=side_effect)

    job = await worker.create_job(media_type="anime", year_start=2020, year_end=2020)

    with patch("src.services.batch_worker.JikanClient", return_value=mock_jikan):
        await worker.run_job(job["job_id"])

    final = await mock_db["batch_import_jobs"].find_one({"job_id": job["job_id"]})
    assert final["status"] == "completed"
    # 4 seasons × 2 unique items = 8 imported, 0 skipped
    assert final["progress"]["imported"] == 8
    assert final["progress"]["skipped"] == 0
    assert final["progress"]["failed"] == 0


# ---------------------------------------------------------------------------
# T052-C: Skip policy — existing mal_ids are not re-imported
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_anime_batch_skips_existing_mal_ids(worker, mock_db):
    # Per-season unique mal_ids so skip policy is clear:
    # mal_id 2001 is pre-inserted → always skipped (4 times); mal_id 2002-2005 are new (1 per season)
    media_service = MediaService(db=mock_db)
    existing_doc = media_service._map_jikan_to_media(_make_jikan_anime(2001), "anime")
    await mock_db["media"].insert_one(existing_doc)

    season_items = {
        "winter": [_make_jikan_anime(2001, "Existing"), _make_jikan_anime(2002, "Winter New")],
        "spring": [_make_jikan_anime(2001, "Existing"), _make_jikan_anime(2003, "Spring New")],
        "summer": [_make_jikan_anime(2001, "Existing"), _make_jikan_anime(2004, "Summer New")],
        "fall":   [_make_jikan_anime(2001, "Existing"), _make_jikan_anime(2005, "Fall New")],
    }

    async def side_effect(year, season):
        return season_items[season]

    mock_jikan = AsyncMock()
    mock_jikan.__aenter__ = AsyncMock(return_value=mock_jikan)
    mock_jikan.__aexit__ = AsyncMock(return_value=False)
    mock_jikan.get_seasonal_anime = AsyncMock(side_effect=side_effect)

    job = await worker.create_job(media_type="anime", year_start=2020, year_end=2020)

    with patch("src.services.batch_worker.JikanClient", return_value=mock_jikan):
        await worker.run_job(job["job_id"])

    final = await mock_db["batch_import_jobs"].find_one({"job_id": job["job_id"]})
    # 4 seasons × 1 existing (skipped) + 1 new → 4 imported, 4 skipped
    assert final["progress"]["imported"] == 4
    assert final["progress"]["skipped"] == 4
    assert final["status"] == "completed"


# ---------------------------------------------------------------------------
# T052-D: Discrete error logging — single failed item logged, batch continues
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_anime_batch_logs_errors_without_crashing(worker, mock_db):
    # Each season: 1 item with missing mal_id (fails) + 1 unique new item (imports)
    raw_broken = {"title": "Broken Item"}  # missing mal_id → will fail

    season_items = {
        "winter": [raw_broken, _make_jikan_anime(3001, "Winter OK")],
        "spring": [raw_broken, _make_jikan_anime(3002, "Spring OK")],
        "summer": [raw_broken, _make_jikan_anime(3003, "Summer OK")],
        "fall":   [raw_broken, _make_jikan_anime(3004, "Fall OK")],
    }

    async def side_effect(year, season):
        return season_items[season]

    mock_jikan = AsyncMock()
    mock_jikan.__aenter__ = AsyncMock(return_value=mock_jikan)
    mock_jikan.__aexit__ = AsyncMock(return_value=False)
    mock_jikan.get_seasonal_anime = AsyncMock(side_effect=side_effect)

    job = await worker.create_job(media_type="anime", year_start=2020, year_end=2020)

    with patch("src.services.batch_worker.JikanClient", return_value=mock_jikan):
        await worker.run_job(job["job_id"])

    final = await mock_db["batch_import_jobs"].find_one({"job_id": job["job_id"]})
    assert final["status"] == "completed"
    # 4 seasons × 1 valid → 4 imported; 4 × 1 broken → 4 failed
    assert final["progress"]["imported"] == 4
    assert final["progress"]["failed"] == 4
    # Error entries in the log
    assert len(final["error_logs"]) == 4


# ---------------------------------------------------------------------------
# T052-E: Pause — worker exits cleanly after pausing mid-batch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_anime_batch_pauses_cleanly(worker, mock_db):
    """
    Simulate pause: after the worker starts and processes the first chunk,
    a concurrent update sets status='paused'. The worker must stop cleanly
    and persist the current_cursor.
    """
    call_count = 0

    async def side_effect_get_season(year, season):
        nonlocal call_count
        call_count += 1
        # After first call, externally pause the job
        if call_count == 1:
            await mock_db["batch_import_jobs"].update_one(
                {"status": "running"},
                {"$set": {"status": "paused"}},
            )
        return [_make_jikan_anime(3000 + call_count)]

    mock_jikan = AsyncMock()
    mock_jikan.__aenter__ = AsyncMock(return_value=mock_jikan)
    mock_jikan.__aexit__ = AsyncMock(return_value=False)
    mock_jikan.get_seasonal_anime = AsyncMock(side_effect=side_effect_get_season)

    job = await worker.create_job(media_type="anime", year_start=2020, year_end=2020)

    with patch("src.services.batch_worker.JikanClient", return_value=mock_jikan):
        await worker.run_job(job["job_id"])

    final = await mock_db["batch_import_jobs"].find_one({"job_id": job["job_id"]})
    # Status must remain paused (worker respected the flag)
    assert final["status"] == "paused"
    # Only 1 season was processed
    assert call_count == 1
    # current_cursor must be saved so resume can continue
    assert final["current_cursor"] is not None


# ---------------------------------------------------------------------------
# T052-F: Resume — job restarts from saved cursor
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_anime_batch_resumes_from_cursor(worker, mock_db):
    """
    Pre-insert a paused job with cursor pointing to 'summer' 2020.
    Resume should start from summer, not from winter.
    """
    job_id = str(uuid.uuid4())
    paused_job = {
        "job_id": job_id,
        "media_type": "anime",
        "year_start": 2020,
        "year_end": 2020,
        "status": "paused",
        "current_cursor": {"year": 2020, "season_index": 2},  # index 2 = 'summer'
        "progress": {
            "total_discovered": 2,
            "imported": 2,
            "skipped": 0,
            "failed": 0,
        },
        "error_logs": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await mock_db["batch_import_jobs"].insert_one(paused_job)

    seasons_called: List[str] = []

    async def side_effect_get_season(year, season):
        seasons_called.append(season)
        return [_make_jikan_anime(4000 + len(seasons_called))]

    mock_jikan = AsyncMock()
    mock_jikan.__aenter__ = AsyncMock(return_value=mock_jikan)
    mock_jikan.__aexit__ = AsyncMock(return_value=False)
    mock_jikan.get_seasonal_anime = AsyncMock(side_effect=side_effect_get_season)

    with patch("src.services.batch_worker.JikanClient", return_value=mock_jikan):
        await worker.resume_job(job_id)

    final = await mock_db["batch_import_jobs"].find_one({"job_id": job_id})
    assert final["status"] == "completed"
    # Should have processed only 'summer' and 'fall' (2 seasons from cursor=2)
    assert seasons_called == ["summer", "fall"]
    # 2 from resumed + 2 pre-existing in progress
    assert final["progress"]["imported"] == 4


# ---------------------------------------------------------------------------
# T052-G: Manga/LN batch — paginates until no next page
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_manga_batch_paginates_all_pages(worker, mock_db):
    page1_data = {
        "data": [_make_jikan_manga(5001), _make_jikan_manga(5002)],
        "pagination": {"has_next_page": True},
    }
    page2_data = {
        "data": [_make_jikan_manga(5003)],
        "pagination": {"has_next_page": False},
    }

    call_count = 0

    async def side_effect_publishing(page=1):
        nonlocal call_count
        call_count += 1
        return page1_data if page == 1 else page2_data

    mock_jikan = AsyncMock()
    mock_jikan.__aenter__ = AsyncMock(return_value=mock_jikan)
    mock_jikan.__aexit__ = AsyncMock(return_value=False)
    mock_jikan.get_manga_publishing = AsyncMock(side_effect=side_effect_publishing)

    job = await worker.create_job(media_type="manga", year_start=2020, year_end=2020)

    with patch("src.services.batch_worker.JikanClient", return_value=mock_jikan):
        await worker.run_job(job["job_id"])

    final = await mock_db["batch_import_jobs"].find_one({"job_id": job["job_id"]})
    assert final["status"] == "completed"
    assert final["progress"]["imported"] == 3
    assert call_count == 2  # 2 pages fetched


# ---------------------------------------------------------------------------
# T052-H: Cursor updated after each chunk
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cursor_updated_after_each_season_chunk(worker, mock_db):
    """Verify that current_cursor is persisted after each chunk via progress counters."""
    season_calls: List[str] = []

    async def side_effect(year, season):
        season_calls.append(season)
        # Return a unique id per season so none are skipped
        return [_make_jikan_anime(9000 + len(season_calls))]

    mock_jikan = AsyncMock()
    mock_jikan.__aenter__ = AsyncMock(return_value=mock_jikan)
    mock_jikan.__aexit__ = AsyncMock(return_value=False)
    mock_jikan.get_seasonal_anime = AsyncMock(side_effect=side_effect)

    job = await worker.create_job(media_type="anime", year_start=2020, year_end=2020)

    with patch("src.services.batch_worker.JikanClient", return_value=mock_jikan):
        await worker.run_job(job["job_id"])

    final = await mock_db["batch_import_jobs"].find_one({"job_id": job["job_id"]})
    # All 4 seasons were processed
    assert len(season_calls) == 4
    assert season_calls == ["winter", "spring", "summer", "fall"]
    # After all chunks, cursor should point past the last season
    assert final["current_cursor"]["season_index"] == 0  # rolled over to next year
    # 4 unique items imported
    assert final["progress"]["imported"] == 4
