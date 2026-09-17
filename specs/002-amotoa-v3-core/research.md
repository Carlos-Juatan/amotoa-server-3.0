# Research & Technical Decisions: Plataforma Pessoal de Gestão de Mídias (Amontoa V3.0)

**Feature Branch**: `002-amotoa-v3-core`  
**Date**: 2026-09-17  
**Status**: Completed  

---

## 1. External Data Source Integration (Jikan API v4)

### Context & Challenge
The platform needs to fetch accurate anime, manga, and light novel metadata without managing its own master media database. Jikan API v4 is a free, public REST API providing data from MyAnimeList. However, Jikan v4 enforces strict rate limits (3 requests per second and 60 requests per minute) and can return HTTP 429 (Too Many Requests) or HTTP 500/503 during upstream load spikes.

### Decision
- **Client**: Use Python `httpx.AsyncClient` with a centralized, rate-limited request dispatcher implementing a Token Bucket algorithm (capped at 2 requests per second to maintain safe headroom).
- **Auto-Retry & Resilience**: Wrap requests with exponential backoff and jitter for HTTP 429, 502, 503, and 504. When a 429 occurs, inspect `Retry-After` header or wait a base time of 3 seconds before retrying up to 5 times.
- **Canonical Identifier**: Use `mal_id` as the primary cross-system identifier. Store canonical Jikan IDs in the local database.
- **Title Hierarchy**: Store both `title_japanese` and `title_english` (plus default `title`). The UI strictly renders `title_japanese` in large font with prominence, and `title_english` below it in a smaller, muted secondary font.
- **Image Handling**: Store exclusively remote image URLs (from Jikan's CDN: `images.webp.large_image_url` or `images.jpg.large_image_url`). Never download or store binary images locally. Provide a local SVG/CSS dark-mode fallback placeholder for missing or broken image URLs.

### Rationale
- Complying strictly with Jikan limits prevents IP blacklisting.
- Storing remote URLs eliminates disk bloat and filesystem management while remaining 100% compliant with FR-023.

### Alternatives Considered
- **AniList GraphQL API**: Evaluated as an alternative. While GraphQL is flexible, Jikan is explicitly chosen by user requirements and matches the MAL ID schema already planned.
- **Local image caching**: Storing thumbnails locally was rejected due to requirement FR-023 ("persist exclusively remote URLs, without storing binary files on local disk").

---

## 2. Multi-Account Dynamic Isolation Architecture (Constitution Principle II)

### Context & Challenge
Constitution Principle II dictates that the hub supports two accounts (`car-j-works` and `car-j-home`) without passwords. Pages have visibility and data isolation settings. Media data must balance catalog deduplication with personalized tracking (watch progress, personal rating, personal tags, custom streaming links, franchise movie watch states).

### Decision
Split the data model into two decoupled MongoDB collections:
1. **`media` collection (Shared Global Catalog)**:
   - Contains immutable canonical data fetched from Jikan: `mal_id`, `media_type` (`anime`, `manga`, `light_novel`), `title_japanese`, `title_english`, `synopsis`, `cover_image_url`, `published_status`, `total_episodes_or_chapters`, `season`, `year`, `franchise_root_id`, `relations`.
   - Accessible by both accounts without data duplication.
2. **`user_progress` collection (Per-Account Isolated Data)**:
   - Partitioned by `account_id` (`car-j-works` or `car-j-home`) and `media_id` (`mal_id`).
   - Contains: `current_progress` (episode or chapter number), `status` (`watching`, `completed`, `on_hold`, `dropped`, `favorite`), `personal_score`, `personal_tags`, `external_links` (custom watch/read URLs), `franchise_movies` (movie watch states for anime), `updated_at`.
   - Queries automatically filter by `account_id` extracted from the incoming request header `X-Active-Account` (defaulting to `car-j-home` if missing).

### Rationale
- Completely adheres to Constitution Principle II: changing accounts seamlessly swaps personal progress, notes, tags, and custom links while preventing duplicate fetching and storage of identical canonical media records.
- Simplifies backup, migration, and maintenance.

### Alternatives Considered
- **Single collection with embedded account maps**: Rejected because document growth becomes unbounded and queries become complex with nested projections.
- **Entirely separate databases per account**: Rejected because base media metadata would be duplicated across databases, multiplying API calls to Jikan during batch imports.

---

## 3. Background Task Execution & Batch Import Queue

### Context & Challenge
The platform requires two types of asynchronous data synchronization:
1. **Seasonal/Periodic Sync**:
   - Animes: Seasonal updates (triggered at the start of Winter, Spring, Summer, Fall, or manually).
   - Mangás & Light Novels: Periodic verification (weekly or monthly, controlled by `MANGA_LN_SYNC_INTERVAL`).
2. **Historical Batch Import**:
   - Defining a year range (e.g., 2005 to 2010), breaking down into season batches (for anime) or weekly/monthly batches (for manga/LN), with pause/resume support, failure logging, and real-time status notifications.

### Decision
- **Scheduler & Worker**: Implement an in-process asynchronous task orchestrator using Python's `asyncio` and a MongoDB-backed job collection (`batch_import_jobs`).
- **Job State Schema**:
  - `job_id`: UUID
  - `media_type`: `anime` | `manga` | `light_novel`
  - `start_year`: int, `end_year`: int
  - `current_pointer`: `{ year: int, batch_index: int, season_or_offset: str }`
  - `status`: `pending` | `running` | `paused` | `completed` | `failed`
  - `progress`: `{ total_items: int, processed_items: int, skipped_items: int, failed_items: int }`
  - `error_log`: list of `{ item_id: int, reason: str, timestamp: datetime }`
- **Pause & Resume**: The worker checks the job's `status` in MongoDB before each chunk. If updated to `paused` via API, the loop cleanly exits after saving `current_pointer`. When resumed, it queries the job and restarts from `current_pointer`.
- **"Ignore and Skip" Policy**: Before inserting any Jikan record, check if `media` already exists with `mal_id`. If so, skip insertion and preserve all associated `user_progress` documents.

### Rationale
- No external heavy dependencies like Redis or Celery needed; Python's native `asyncio` combined with MongoDB state persistence ensures low footprint and zero cloud dependencies (Constitution Principle I).

### Alternatives Considered
- **Celery + Redis**: Rejected as over-engineering for a local single-user system; violates the self-contained simplicity principle.
- **Pure in-memory threading**: Rejected because restarting the FastAPI server would lose batch job progress and prevent reliable resume.

---

## 4. Franchise & Season Relationship Resolution

### Context & Challenge
Users need to see all related seasons and installments of a title consolidated into a single Detail Page, rather than fragmented entries. Jikan provides `/anime/{id}/relations` and `/manga/{id}/relations` returning entries like `Sequel`, `Prequel`, `Spin-off`, `Side story`.

### Decision
- When ingesting a media item (or viewing its details), inspect the `/relations` payload.
- Filter relations for direct lineage: `Sequel`, `Prequel`, `Alternative version`, `Parent story`.
- Determine or assign a `franchise_root_id` (the earliest known `mal_id` in the lineage chain).
- All media items sharing the same `franchise_root_id` are grouped together in the Detail Page, sorted chronologically by release date or season year.

### Rationale
- Delivers a unified overview of all seasons without manual cataloging.
- Gracefully degrades if an upstream relation is missing or circular.

### Alternatives Considered
- **Manual user grouping**: Too labor-intensive for hundreds of anime.
- **Strict title string similarity**: Unreliable for Japanese media where titles change drastically between seasons (e.g., *Working!!* vs *Working'!!*).

---

## 5. Daily Database Backup Strategy (FR-024)

### Context & Challenge
FR-024 requires automatic, daily compressed backups of the local MongoDB database to a designated directory (`BACKUP_DIR`), running locally without manual intervention.

### Decision
- **Mechanism**: A background scheduled task in FastAPI (or `APScheduler`) running every 24 hours at 03:00 (or on startup if the last backup is older than 24h).
- **Execution**: The service utilizes `motor` to dump all collections (`accounts_config`, `media`, `user_progress`, `batch_import_jobs`) into a compressed `.tar.gz` archive containing JSON/BSON records, named `amotoa_backup_YYYYMMDD_HHMMSS.tar.gz`.
- **Location**: Default path `/backups` inside the container or mounted host directory configured via `BACKUP_DIR`.
- **Retention**: Retain the last 14 daily backups, automatically pruning older archives to conserve disk space.

### Rationale
- Using Python-native compression (`tarfile` + `gzip`) avoids hard dependencies on `mongodump` binaries being installed inside the container environment.
- Works seamlessly across Docker containers and native host environments.

---

## 6. Frontend Architecture & Modular Component Factory (Constitution Principle V & III)

### Context & Challenge
Constitution Principle V mandates strict modularity and Factory Pattern architecture. The platform features three distinct showcases (`/animes`, `/mangas`, `/light-novels`), each with sub-pages:
- Detail Page (`/:type/:id`)
- Daily Progress Module (`/:type/progress`)

While the three media types share common UI structures (carousels, cards, dark theme, hover popups), they have deliberate behavioral variations:
- **Animes**: tracks episodes, seasonal releases, includes Franchise Movies block.
- **Mangás**: tracks chapters, filtered by `Publishing` status, no franchise movies.
- **Light Novels**: tracks chapters, filtered by `Publishing` status, no franchise movies.

### Decision
- **Media Configuration Factory (`getMediaConfig(type)`)**:
  Provides type-specific definitions, endpoints, unit labels ("Episódio" vs "Capítulo"), filter rules, and feature flags (`hasFranchiseMovies: boolean`).
- **Showcase Factory Component (`MediaShowcaseView`)**:
  Generic base view parameterized with `mediaConfig`. Dynamically renders carousels grouped by tracking status:
  - "Em andamento"
  - "Favoritos"
  - "Pausados"
  - "Planejados / Não iniciados"
- **Detail View Component (`MediaDetailView`)**:
  Displays prominent Japanese title + secondary English title, unified seasons/franchise block, official image carousel with full-screen modal, and conditionally renders the Franchise Movies block only when `type === 'anime'`.
- **Daily Progress View Component (`DailyProgressView`)**:
  Restricted to active media:
  - Anime: currently airing in the current season + status "Em andamento".
  - Manga/LN: status `Publishing` + status "Em andamento".
  Features: `+1` quick increment, exact selector dropdown (with max validation), and external streaming/reading link launcher (`target="_blank"`).
- **Aesthetic System**:
  Built on Tailwind CSS + glassmorphism (`glass-card`, `glass-panel`), dark slate palette (`#090d16`, `#0f172a`), electric blue/indigo accents, and smooth hover micro-animations.
