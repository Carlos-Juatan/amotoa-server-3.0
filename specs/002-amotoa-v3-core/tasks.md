---

description: "Task list for Plataforma Pessoal de Gestão de Mídias (Amontoa V3.0) implementation"
---

# Tasks: Plataforma Pessoal de Gestão de Mídias (Amontoa V3.0)

**Input**: Design documents from `/specs/002-amotoa-v3-core/`
**Prerequisites**: [plan.md](file:///mnt/D_DADOS/02_Projetos_Ativos/daily_user/amotoa-server-3.0/specs/002-amotoa-v3-core/plan.md), [spec.md](file:///mnt/D_DADOS/02_Projetos_Ativos/daily_user/amotoa-server-3.0/specs/002-amotoa-v3-core/spec.md), [data-model.md](file:///mnt/D_DADOS/02_Projetos_Ativos/daily_user/amotoa-server-3.0/specs/002-amotoa-v3-core/data-model.md), [contracts/openapi.yaml](file:///mnt/D_DADOS/02_Projetos_Ativos/daily_user/amotoa-server-3.0/specs/002-amotoa-v3-core/contracts/openapi.yaml), [research.md](file:///mnt/D_DADOS/02_Projetos_Ativos/daily_user/amotoa-server-3.0/specs/002-amotoa-v3-core/research.md), [quickstart.md](file:///mnt/D_DADOS/02_Projetos_Ativos/daily_user/amotoa-server-3.0/specs/002-amotoa-v3-core/quickstart.md)

**Tests**: Unit and integration test tasks are included to guarantee robustness of data isolation, rate limiting resilience, and API contract fidelity.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3...)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency management, and core configuration

- [ ] T001 Update backend dependencies (fastapi, motor, pydantic, httpx, pytest, pytest-asyncio) in `backend/requirements.txt`
- [ ] T002 [P] Verify and update frontend dependencies (lucide-react, clsx, tailwindcss) in `frontend/package.json`
- [ ] T003 [P] Setup environment variable definitions and configuration in `backend/src/core/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database connections, schemas, error handling, and API client layer that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup MongoDB database client factory (`get_database()`), collections, and index initialization in `backend/src/core/database.py` per Constitution Principle V
- [ ] T005 [P] Create shared media Pydantic schemas in `backend/src/api/schemas/media.py`
- [ ] T006 [P] Create user progress Pydantic schemas in `backend/src/api/schemas/progress.py`
- [ ] T007 [P] Create batch jobs and backup Pydantic schemas in `backend/src/api/schemas/batch.py`
- [ ] T008 [P] Implement application exceptions and error handlers in `backend/src/core/exceptions.py`
- [ ] T009 [P] Verify and validate X-Active-Account header dependency in `backend/src/api/dependencies.py`
- [ ] T010 [P] Verify centralized frontend API client with X-Active-Account header handling in `frontend/src/services/api.ts`
- [ ] T011 [P] Implement Media Showcase Configuration Factory in `frontend/src/services/mediaConfig.ts`
- [ ] T012 [P] Verify and integrate active account switching state hook in `frontend/src/hooks/useActiveAccount.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Vitrine e Navegação em Carrossel (Priority: P1) 🎯 MVP

**Goal**: Enable the administrator to access type-specific showcases (`/animes`, `/manga`, `/light_novels`) from the dashboard, displaying media in horizontal carousels grouped by tracking status ("Em andamento", "Favoritos", "Pausados"), with Japanese title prominently emphasized and English title secondarily below, plus quick info hover popup.

**Independent Test**: Seed local MongoDB with sample media and progress records; navigate to `/animes`, verify status carousels render smoothly at 60fps in fixed dark mode, hover triggers quick info popup, and clicking a card redirects to the detail page.

### Tests for User Story 1

- [ ] T013 [P] [US1] Create unit and integration tests for media showcase endpoint in `backend/tests/test_media_router.py`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement MediaService catalog querying and carousel status grouping in `backend/src/services/media_service.py`
- [ ] T015 [US1] Implement GET /api/media/{media_type} router endpoint in `backend/src/api/routers/media.py`
- [ ] T016 [P] [US1] Implement fallback placeholder image component with dark mode styling in `frontend/src/components/common/PlaceholderImage.tsx`
- [ ] T017 [P] [US1] Implement hover quick info popup component in `frontend/src/components/MediaQuickInfoHover.tsx`
- [ ] T018 [P] [US1] Implement MediaCard component with Japanese primary and English secondary title hierarchy in `frontend/src/components/MediaCard.tsx`
- [ ] T019 [US1] Implement horizontal scrolling MediaCarousel component with arrow navigation in `frontend/src/components/MediaCarousel.tsx`
- [ ] T020 [US1] Implement useMediaShowcase data fetching hook in `frontend/src/hooks/useMediaShowcase.ts`
- [ ] T021 [US1] Implement parameterized MediaShowcasePage using mediaConfig in `frontend/src/pages/MediaShowcasePage.tsx`
- [ ] T022 [US1] Wire /animes, /manga, and /light_novels routes to MediaShowcasePage in `frontend/src/App.tsx`

**Checkpoint**: At this point, User Story 1 is fully functional and delivers the core showcase MVP.

---

## Phase 4: User Story 5 - Página de Detalhes Unificada (Priority: P1)

**Goal**: Display comprehensive unified details for any media item, uniting all franchise seasons (derived from Jikan Sequel/Prequel relations) under a single visual block, official image gallery carousel with full-screen zoom modal, and boundary-aware lateral navigation between titles in the group.

**Independent Test**: Open `/animes/:id` for a multi-season title; verify all seasons appear unified in a single block, images navigate horizontally and enlarge upon click, and lateral arrows navigate across adjacent titles with end-of-list boundary disabling.

### Tests for User Story 5

- [ ] T023 [P] [US5] Add tests for unified detail and franchise relations endpoint in `backend/tests/test_media_router.py`

### Implementation for User Story 5

- [ ] T024 [P] [US5] Implement franchise root grouping and relations resolution logic in `backend/src/services/media_service.py`
- [ ] T025 [US5] Implement GET /api/media/{media_type}/{mal_id} router endpoint in `backend/src/api/routers/media.py`
- [ ] T026 [P] [US5] Create full-screen image gallery modal component in `frontend/src/components/ImageGalleryModal.tsx`
- [ ] T027 [P] [US5] Create FranchiseRelations component for unified season display in `frontend/src/components/FranchiseRelations.tsx`
- [ ] T028 [US5] Implement MediaDetailPage with metadata, Japanese title prominence, gallery carousel, and boundary-aware navigation arrows in `frontend/src/pages/MediaDetailPage.tsx`
- [ ] T029 [US5] Wire /:type/:id route to MediaDetailPage in `frontend/src/App.tsx`

**Checkpoint**: At this point, User Stories 1 AND 5 provide end-to-end showcase-to-detail exploration.

---

## Phase 5: User Story 6 - Gestão de Progresso, Links Externos, Notas e Tags (Priority: P1)

**Goal**: Allow administrator on the Detail Page to update tracking progress (episodes for anime, chapters for manga/LN), score, tags, external streaming/reading links, and manage anime franchise movies (automatically hidden for manga/LN).

**Independent Test**: On Detail Page, change progress value, edit personal score and tags, add an external link, and (for anime) add/toggle a franchise movie; refresh page to confirm all changes are persisted immediately per active account (`car-j-works` or `car-j-home`).

### Tests for User Story 6

- [ ] T030 [P] [US6] Add tests for progress, tags, links, and movie endpoints in `backend/tests/test_progress_router.py`

### Implementation for User Story 6

- [ ] T031 [P] [US6] Implement ProgressService methods for progress, scores, tags, external links, and movie watch toggles in `backend/src/services/progress_service.py`
- [ ] T032 [US6] Implement progress update endpoints under /api/media/{media_type}/{mal_id}/ (PUT /progress, PUT /links, PUT /tags, POST /movies, PATCH /movies/{movie_id}) in `backend/src/api/routers/progress.py`
- [ ] T033 [P] [US6] Create FranchiseMoviesList component for anime-exclusive movie management in `frontend/src/components/FranchiseMoviesList.tsx`
- [ ] T034 [US6] Implement progress tracker widgets, score inputs, tag management, and external links editor in `frontend/src/pages/MediaDetailPage.tsx`

**Checkpoint**: At this point, full catalog interaction and per-account tracking persistence is operational.

---

## Phase 6: User Story 7 - Acompanhamento de Progresso Diário (Priority: P1)

**Goal**: Provide a streamlined daily progress tracking module (`/:type/progress`) restricted to active media (current season for Anime; `Publishing` status for Manga/LN), with instant "+1" increment, exact selector dropdown with upper limit validation, and quick external link opening in a new tab.

**Independent Test**: Navigate to `/animes/progress`; verify active ongoing anime appear, click "+1" to increment episode count instantly, select specific episode in dropdown, verify values above total episodes are blocked, and verify completion automatically removes finished media. Verify friendly empty state when no active media exists.

### Tests for User Story 7

- [ ] T035 [P] [US7] Add tests for active progress filtering and quick increment in `backend/tests/test_progress_router.py`

### Implementation for User Story 7

- [ ] T036 [P] [US7] Implement active progress querying and unit increment logic in `backend/src/services/progress_service.py`
- [ ] T037 [US7] Implement GET /api/media/{media_type}/active-progress and POST /api/media/{media_type}/{mal_id}/increment in `backend/src/api/routers/progress.py`
- [ ] T038 [P] [US7] Create DailyProgressCard component with +1 button, bounded dropdown selector, and external link action in `frontend/src/components/DailyProgressCard.tsx`
- [ ] T039 [US7] Implement DailyProgressPage with active media list, empty state encouragement, and showcase shortcut in `frontend/src/pages/DailyProgressPage.tsx`
- [ ] T040 [US7] Wire /:type/progress route to DailyProgressPage in `frontend/src/App.tsx`

**Checkpoint**: The daily routine workflow is complete and testable independently.

---

## Phase 7: User Story 3 - Sincronização Automática de Novos Lançamentos (Priority: P1)

**Goal**: Connect to Jikan API v4 with token bucket rate limiting (2 req/s) and auto-retry to sync new seasonal animes (at season start or manual trigger) and periodic manga/LN releases (interval via `MANGA_LN_SYNC_INTERVAL`), skipping existing media and preserving all user data.

**Independent Test**: Simulate external sync call with existing and new media; verify new media is ingested into MongoDB while existing items retain 100% of user progress, personal notes, and tags. Verify rate limiting handles 429 retries gracefully.

### Tests for User Story 3

- [ ] T041 [P] [US3] Create unit tests for JikanClient token bucket rate limiting and retry backoff in `backend/tests/test_jikan_client.py`

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement JikanClient with httpx AsyncClient, token bucket dispatcher (2 req/s), and exponential backoff retry in `backend/src/services/jikan_client.py`
- [ ] T043 [US3] Implement seasonal sync for anime and periodic sync for manga/LN with Ignore & Skip policy in `backend/src/services/media_service.py`
- [ ] T044 [US3] Implement manual sync trigger endpoint POST /api/media/sync/{media_type} in `backend/src/api/routers/media.py`
- [ ] T045 [US3] Configure background periodic sync scheduler using MANGA_LN_SYNC_INTERVAL in `backend/src/core/scheduler.py`

**Checkpoint**: Automated and resilient upstream sync keeps catalog populated without user intervention.

---

## Phase 8: User Story 2 - Pesquisa, Filtros e Ordenação do Catálogo (Priority: P2)

**Goal**: Enable multi-field catalog search (Japanese title, English title, tags), filters (genre, season/year, initial letter), and multi-criteria sorting (title, public score, personal score, release year), plus external Jikan search fallback with 1-click import into local catalog.

**Independent Test**: Search for local media by Japanese or English partial name; apply genre and year filters; verify sorting changes order; search an uncataloged title via external Jikan search and click import, verifying it appears in the local showcase.

### Tests for User Story 2

- [ ] T046 [P] [US2] Add tests for catalog search, filtering, and external import endpoints in `backend/tests/test_media_router.py`

### Implementation for User Story 2

- [ ] T047 [US2] Implement multi-attribute filtering and text search query builders in `backend/src/services/media_service.py`
- [ ] T048 [US2] Implement GET /api/media/external/search and POST /api/media/external/import in `backend/src/api/routers/media.py`
- [ ] T049 [P] [US2] Create SearchBar component with local results and external Jikan search fallback trigger in `frontend/src/components/SearchBar.tsx`
- [ ] T050 [P] [US2] Create CatalogFilterBar component with genre, year, initial letter, and sorting options in `frontend/src/components/CatalogFilterBar.tsx`
- [ ] T051 [US2] Integrate SearchBar and CatalogFilterBar into `frontend/src/pages/MediaShowcasePage.tsx`

**Checkpoint**: High-power search, filtering, and ad-hoc single media import are operational.

---

## Phase 9: User Story 4 - Importação em Lote de Anos Anteriores (Priority: P2)

**Goal**: Allow administrator to initiate historical batch imports by year range in the background (divided into seasons for anime, weekly/monthly for manga/LN), with pause/resume support, top bar status notification, and failure logging.

**Independent Test**: Start a batch import for a 2-year range; click pause, verify job state pauses and pointer is preserved; click resume, verify job resumes from saved cursor; simulate transient error and confirm error is isolated in the discrete failure log without crashing the batch.

### Tests for User Story 4

- [ ] T052 [P] [US4] Create unit and integration tests for batch worker lifecycle and resume in `backend/tests/test_batch_worker.py`

### Implementation for User Story 4

- [ ] T053 [P] [US4] Implement BatchWorker with cursor progression, chunking, pause/resume state checking, and discrete error logging in `backend/src/services/batch_worker.py`
- [ ] T054 [US4] Implement batch job endpoints (GET /api/batch-jobs, POST /api/batch-jobs, POST /api/batch-jobs/{id}/pause, POST /api/batch-jobs/{id}/resume) in `backend/src/api/routers/batch_jobs.py`
- [ ] T055 [P] [US4] Create BatchImportModal component with year range pickers, progress bar, pause/resume controls, and error log viewer in `frontend/src/components/BatchImportModal.tsx`
- [ ] T056 [P] [US4] Create background job notification indicator in `frontend/src/components/Navbar.tsx`
- [ ] T057 [US4] Integrate BatchImportModal toggle and notification indicator into the application header in `frontend/src/App.tsx`

**Checkpoint**: Historical ingestion enables deep archive collection resupply safely.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Automated daily compressed backups (FR-024), router registrations in FastAPI, WIP placeholder cleanups, and end-to-end verification

- [ ] T058 [P] Create unit tests for backup creation, retention pruning, and recovery logging in `backend/tests/test_backup_service.py`
- [ ] T059 [P] Implement daily compressed MongoDB backup service (FR-024) with 14-day retention in `backend/src/services/backup_service.py`
- [ ] T060 Implement admin backup endpoints (GET /api/admin/backups, POST /api/admin/backups) in `backend/src/api/routers/admin.py`
- [ ] T061 Register all new routers (media, progress, batch_jobs, admin) and initialize background schedulers in `backend/src/main.py`
- [ ] T062 [P] Clean up obsolete WIP placeholders for animes, manga, and light novels in `frontend/src/pages/WIPPage.tsx`
- [ ] T063 Run end-to-end test suite, latency benchmark (<50ms for local endpoints, SC-004), and build validation per quickstart.md (pytest tests/ -v, npm run lint, npm run build)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
  - **User Story 1 (P1 - MVP)**: Starts immediately after Phase 2.
  - **User Story 5 (P1)**: Depends on Phase 2; integrates with US1 navigation.
  - **User Story 6 (P1)**: Depends on US5 (Detail Page structure) and Phase 2.
  - **User Story 7 (P1)**: Depends on US6 (Progress data structure) and Phase 2.
  - **User Story 3 (P1)**: Depends on Phase 2; can be implemented in parallel with frontend stories.
  - **User Story 2 (P2)**: Depends on US1 (Showcase view) and US3 (JikanClient).
  - **User Story 4 (P2)**: Depends on US3 (JikanClient) and Phase 2.
- **Polish (Phase 10)**: Depends on all user stories being implemented.

### Parallel Opportunities

- Within Phase 1: T002 and T003 can execute in parallel.
- Within Phase 2: T005, T006, T007, T008, T009, T010, T011, and T012 can all execute in parallel once T004 is established.
- Within User Story 1: T013, T014, T016, T017, and T018 can all proceed in parallel.
- Within User Story 5: T023, T024, T026, and T027 can proceed in parallel.
- Within User Story 6: T030, T031, and T033 can proceed in parallel.
- Within User Story 7: T035, T036, and T038 can proceed in parallel.
- Within User Story 3: T041 and T042 can proceed in parallel.
- Within User Story 2: T046, T049, and T050 can proceed in parallel.
- Within User Story 4: T052, T053, T055, and T056 can proceed in parallel.
- Within Phase 10: T058, T059, and T062 can proceed in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch test task and component tasks in parallel:
Task: "Create unit and integration tests for media showcase endpoint in backend/tests/test_media_router.py"
Task: "Implement fallback placeholder image component with dark mode styling in frontend/src/components/common/PlaceholderImage.tsx"
Task: "Implement hover quick info popup component in frontend/src/components/MediaQuickInfoHover.tsx"
Task: "Implement MediaCard component with Japanese primary and English secondary title hierarchy in frontend/src/components/MediaCard.tsx"
```

## Parallel Example: User Story 5

```bash
# Launch test task and UI components for Detail Page in parallel:
Task: "Add tests for unified detail and franchise relations endpoint in backend/tests/test_media_router.py"
Task: "Create full-screen image gallery modal component in frontend/src/components/ImageGalleryModal.tsx"
Task: "Create FranchiseRelations component for unified season display in frontend/src/components/FranchiseRelations.tsx"
```

## Parallel Example: User Story 6

```bash
# Launch backend test, backend service, and frontend movie component in parallel:
Task: "Add tests for progress, tags, links, and movie endpoints in backend/tests/test_progress_router.py"
Task: "Implement ProgressService methods for progress, scores, tags, external links, and movie watch toggles in backend/src/services/progress_service.py"
Task: "Create FranchiseMoviesList component for anime-exclusive movie management in frontend/src/components/FranchiseMoviesList.tsx"
```

## Parallel Example: User Story 7

```bash
# Launch test, service query, and progress card component in parallel:
Task: "Add tests for active progress filtering and quick increment in backend/tests/test_progress_router.py"
Task: "Implement active progress querying and unit increment logic in backend/src/services/progress_service.py"
Task: "Create DailyProgressCard component with +1 button, bounded dropdown selector, and external link action in frontend/src/components/DailyProgressCard.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001 - T003).
2. Complete Phase 2: Foundational (T004 - T012).
3. Complete Phase 3: User Story 1 (T013 - T022).
4. **STOP and VALIDATE**: Seed MongoDB, run backend tests, load `/animes` showcase, verify smooth 60fps carousels and card popups.

### Incremental Delivery

1. **Increment 1 (MVP)**: Setup + Foundation + Showcase Carousel (`/animes`, `/manga`, `/light_novels`).
2. **Increment 2**: Detail Page with Unified Franchise Seasons & Gallery Modal (US5).
3. **Increment 3**: Detail Page Progress Tracking, Notes, Tags, Links, and Anime Movies (US6).
4. **Increment 4**: Frictionless Daily Progress Module with +1 Increment and Dropdown (US7).
5. **Increment 5**: Jikan API v4 Integration with Token Bucket Rate Limiting & Seasonal/Periodic Sync (US3).
6. **Increment 6**: Search Bar, Filter Bar, and External Jikan Import (US2).
7. **Increment 7**: Historical Year Range Batch Import with Pause/Resume (US4).
8. **Increment 8**: Automated Compressed MongoDB Backups & Polish (Phase 10).

### Parallel Team Strategy

- **Backend Engineer**: Focuses on T004-T009 (Foundation), T014-T015 (Media API), T024-T025 (Detail API), T031-T032 (Progress API), T041-T045 (Jikan Client & Sync), T053-T054 (Batch Worker), T059-T061 (Backups).
- **Frontend Engineer**: Focuses on T010-T012 (Client & Factory), T016-T022 (Showcase), T026-T029 (Detail & Modal), T033-T034 (Detail Widgets), T038-T040 (Daily Progress View), T049-T051 (Search/Filters), T055-T057 (Batch Modal).

---

## Notes

- `[P]` tasks target different files with no incomplete prerequisites.
- `[Story]` label (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`, `[US6]`, `[US7]`) ensures direct traceability back to user acceptance criteria in `spec.md`.
- Japanese title hierarchy (FR-026) is preserved as primary display throughout all components.
- Image storage rules (FR-023) are respected with remote CDN URLs and SVG dark mode placeholders.
- Anime-exclusive franchise movies (FR-015, FR-017) are strictly isolated from manga and light novels.
