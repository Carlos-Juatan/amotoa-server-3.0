# Data Model Specification: Plataforma Pessoal de Gestão de Mídias (Amontoa V3.0)

**Feature Branch**: `002-amotoa-v3-core`  
**Date**: 2026-09-17  
**Status**: Draft  

---

## 1. Overview & Storage Strategy

Amontoa V3.0 persists data in an external MongoDB instance accessed via `MONGODB_URI`. In compliance with Constitution Principle II (Multi-Account Dynamic Isolation) and Requirement FR-023 (Local storage without binary image downloads):
- **`media` collection**: Canonical, immutable metadata retrieved from Jikan API v4. Shared across all accounts to eliminate redundancy.
- **`user_progress` collection**: User tracking state (current episode/chapter, watch status, personal rating, personal tags, external streaming/reading links, franchise movie watch states). Partitioned by `account_id` (`car-j-works` or `car-j-home`).
- **`batch_import_jobs` collection**: Execution records for background batch imports with cursor positions and failure logs.
- **`backups_log` collection**: Registry of automated daily backup archives with verification timestamps.

---

## 2. Entities & Schemas

### 2.1 Media (Obra)
Represents canonical media entries (Animes, Mangás, Light Novels).

**Collection**: `media`

| Field | Type | Required | Description / Rules |
|---|---|---|---|
| `_id` | ObjectId | Yes | Internal MongoDB primary key |
| `mal_id` | Integer | Yes | Unique canonical identifier from Jikan API / MyAnimeList (Unique Index) |
| `type` | String | Yes | Enum: `'anime'`, `'manga'`, `'light_novel'`. Indexed |
| `title_japanese` | String | Yes | Japanese title (Primary display title, emphasized in UI) |
| `title_english` | String | No | English title (Secondary display title, smaller font under Japanese) |
| `title_default` | String | Yes | Romaji or default title from upstream |
| `synopsis` | String | No | Full plot summary or description |
| `cover_image_url` | String | Yes | Remote CDN URL (`large_image_url` from WebP or JPG). Remote only (FR-023) |
| `gallery_image_urls`| Array[String] | No | Remote CDN URLs for official artwork/screenshots |
| `published_status` | String | Yes | Upstream release status: `'Publishing'`, `'Finished'`, `'Currently Airing'`, `'Not yet aired'` |
| `total_units` | Integer | No | Total episodes (anime) or chapters (manga/LN). Null if unknown/ongoing |
| `season` | String | No | Launch season: `'winter'`, `'spring'`, `'summer'`, `'fall'` (anime only) |
| `year` | Integer | No | Launch year (e.g., 2024). Indexed |
| `genres` | Array[String] | No | Upstream genre/theme tags (e.g., `["Action", "Fantasy"]`) |
| `score_public` | Float | No | Global public score from Jikan (0.0 to 10.0) |
| `franchise_root_id`| Integer | No | `mal_id` of the root/first installment for unified season grouping |
| `relations` | Array[Relation]| No | Direct lineage links (`Sequel`, `Prequel`, `Spin-off`) |
| `created_at` | DateTime | Yes | Timestamp of catalog ingestion |
| `updated_at` | DateTime | Yes | Timestamp of last upstream refresh |

#### Subdocument: Relation
```json
{
  "mal_id": 12345,
  "type": "anime",
  "relation_type": "Sequel",
  "title": "Season 2"
}
```

**Indexes**:
- `{ "mal_id": 1 }` (Unique)
- `{ "type": 1, "year": -1 }`
- `{ "type": 1, "published_status": 1 }`
- `{ "franchise_root_id": 1 }`
- Text index: `{ "title_japanese": "text", "title_english": "text", "title_default": "text", "synopsis": "text" }`

---

### 2.2 UserProgress (Progresso e Gestão Pessoal)
Tracks an account's personal interaction with a specific media item.

**Collection**: `user_progress`

| Field | Type | Required | Description / Rules |
|---|---|---|---|
| `_id` | ObjectId | Yes | Internal MongoDB primary key |
| `account_id` | String | Yes | Account identifier: `'car-j-works'` or `'car-j-home'`. Indexed |
| `media_mal_id` | Integer | Yes | Foreign key referencing `media.mal_id`. Indexed |
| `media_type` | String | Yes | Denormalized type (`'anime'`, `'manga'`, `'light_novel'`) for fast queries |
| `current_unit` | Integer | Yes | Current episode (anime) or chapter (manga/LN). Default: `0` |
| `status` | String | Yes | Personal status: `'watching'` ("Em andamento"), `'completed'` ("Finalizado"), `'on_hold'` ("Pausado"), `'dropped'` ("Dropado"), `'plan_to_watch'` ("Planejado") |
| `is_favorite` | Boolean | Yes | Quick favorite toggle. Default: `false` |
| `personal_score` | Integer | No | Score from `0` to `10` |
| `personal_tags` | Array[String] | Yes | User-defined custom tags (e.g., `["Rever", "Masterpiece"]`) |
| `external_links` | Array[ExternalLink]| Yes | User-provided streaming/reading URLs |
| `franchise_movies` | Array[FranchiseMovie]| No | Movie tracking list (Applicable exclusively to `anime` media) |
| `last_interacted_at`| DateTime | Yes | Timestamp of latest progress update |
| `completed_at` | DateTime | No | Timestamp when `status` moved to `'completed'` |

#### Subdocument: ExternalLink
```json
{
  "label": "Crunchyroll",
  "url": "https://www.crunchyroll.com/series/..."
}
```

#### Subdocument: FranchiseMovie (Anime Only)
```json
{
  "movie_id": "uuid-string",
  "title": "Mugen Train",
  "cover_image_url": "https://...",
  "watched": true,
  "release_year": 2020
}
```

**Indexes**:
- `{ "account_id": 1, "media_mal_id": 1 }` (Unique compound index)
- `{ "account_id": 1, "media_type": 1, "status": 1 }`
- `{ "account_id": 1, "is_favorite": 1 }`

---

### 2.3 BatchImportJob (Trabalho de Importação em Lote)
Manages long-running historical imports of media by year range.

**Collection**: `batch_import_jobs`

| Field | Type | Required | Description / Rules |
|---|---|---|---|
| `_id` | ObjectId | Yes | Internal MongoDB primary key |
| `job_id` | String | Yes | Unique UUID for client polling |
| `media_type` | String | Yes | Enum: `'anime'`, `'manga'`, `'light_novel'` |
| `year_start` | Integer | Yes | Beginning of year range (e.g., `2005`) |
| `year_end` | Integer | Yes | End of year range (e.g., `2008`) |
| `status` | String | Yes | Enum: `'pending'`, `'running'`, `'paused'`, `'completed'`, `'failed'` |
| `current_cursor` | Object | Yes | Resume pointer: `{ "year": 2006, "batch_step": "spring", "page": 2 }` |
| `progress` | Object | Yes | Counters: `{ "total_discovered": 120, "imported": 110, "skipped": 8, "failed": 2 }` |
| `error_logs` | Array[ErrorEntry] | Yes | Discrete failure logs per media |
| `created_at` | DateTime | Yes | Creation timestamp |
| `updated_at` | DateTime | Yes | Last heartbeat / progress save |

#### Subdocument: ErrorEntry
```json
{
  "mal_id": 9999,
  "title": "Unknown OVA",
  "reason": "HTTP 404 upstream or rate limit exhausted",
  "timestamp": "2026-09-17T18:30:00Z"
}
```

**Indexes**:
- `{ "job_id": 1 }` (Unique)
- `{ "status": 1 }`

---

## 3. State Transitions & Validation Rules

### 3.1 Progress State Machine
```
[Not Started] (current_unit: 0)
     │
     ▼ (Click "+1" or dropdown select > 0)
['watching'] ("Em andamento")
     │
     ├─────────────────────────────────────────┐
     ▼ (current_unit reaches total_units OR manual mark)  ▼ (User pauses/drops)
['completed'] ("Finalizado")             ['on_hold'] / ['dropped']
     │                                         │
     └─────────────────┬───────────────────────┘
                       ▼ (User reactivates)
                 ['watching']
```

### 3.2 Validation Rules
1. **Unit Bounds**: `current_unit >= 0`. If `total_units` is defined and > 0, `current_unit <= total_units`. Dropdown selector must disable or reject values > `total_units`.
2. **Title Primacy**: Every media representation must preserve `title_japanese` as the primary key. If Jikan does not provide a Japanese title, fallback to `title_default`.
3. **Franchise Movies**: Franchise movies are strictly invalid for `manga` and `light_novel` media types. Any API payload attempting to inject movies for manga/LN is rejected.
4. **Idempotent Ingestion**: Ingesting an already existing `mal_id` updates only public metadata (`score_public`, `synopsis`) and NEVER overwrites `user_progress`.
