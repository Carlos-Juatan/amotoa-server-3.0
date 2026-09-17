# Implementation Plan: Plataforma Pessoal de Gestão de Mídias (Amontoa V3.0)

**Branch**: `002-amotoa-v3-core` | **Date**: 2026-09-17 | **Spec**: [spec.md](file:///mnt/D_DADOS/02_Projetos_Ativos/daily_user/amotoa-server-3.0/specs/002-amotoa-v3-core/spec.md)
**Input**: Feature specification from `/specs/002-amotoa-v3-core/spec.md`

## Summary

Implement the core personal media tracking and cataloging platform (Amontoa V3.0) for Animes, Mangás, and Light Novels. The feature provides three dedicated showcases (`/animes`, `/manga`, `/light_novels`) replacing WIP placeholders, a Detail Page with unified franchise seasons and image galleries, a frictionless Daily Progress Module for tracking active ongoing media (+1 quick increment and exact selector), Jikan API v4 integration with auto-retry queue, background batch imports with pause/resume, and automated daily compressed MongoDB backups.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), Node 20+ / TypeScript ~5.4+ (Frontend)  
**Primary Dependencies**: FastAPI 0.100+, Motor 3.2+, Pydantic 2.0+, httpx 0.24+, Vite 8+, Tailwind CSS 3.4+, Lucide React 0.460+  
**Storage**: MongoDB (External instance on host accessed via `MONGODB_URI`)  
**Testing**: pytest, pytest-asyncio, httpx test client (Backend), ESLint, Vitest (Frontend)  
**Target Platform**: Linux (Localhost-first / Docker Swarm containerized services)  
**Project Type**: Web application (FastAPI backend + Vite React SPA frontend)  
**Performance Goals**: Local API latency < 50ms, carousel rendering at 60fps, background sync non-blocking  
**Constraints**: Jikan rate limit compliance (2 req/s safe token bucket), offline-first local catalog caching, remote image URLs only (no local binary files), fixed dark mode  
**Scale/Scope**: Single developer personal hub, 2 isolated accounts (`car-j-works` and `car-j-home`), 3 showcase domains, ~1000s catalog items  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Localhost & Docker Swarm-First (Self-Contained)**:
  - **Status**: PASS
  - **Verification**: Services are containerized for Docker Swarm without external cloud dependencies. External MongoDB instance running on host is accessed via `MONGODB_URI`.
- **Principle II: Multi-Account Dynamic Isolation**:
  - **Status**: PASS
  - **Verification**: Base media metadata (`media` collection) is shared to avoid redundant API queries, while personal progress, notes, tags, custom links, and franchise movie watch statuses (`user_progress` collection) are strictly isolated by `account_id` based on the `X-Active-Account` header.
- **Principle III: Premium Developer-Centric Aesthetics (Tailwind + Shadcn)**:
  - **Status**: PASS
  - **Verification**: Built with Tailwind CSS and glassmorphic styling (`glass-card`, `glass-panel`). Native dark palette, Japanese/English title hierarchy, and micro-animations for hover states and modals.
- **Principle IV: Incremental WIP Activation (Single-Page MVP)**:
  - **Status**: PASS
  - **Verification**: Replaces WIP placeholders for `animes`, `manga`, and `light_novels` while leaving the remaining 9 hub utilities untouched.
- **Principle V: Strict Modularity & Factory Pattern Architecture**:
  - **Status**: PASS
  - **Verification**: Backend structures routers (`media`, `progress`, `batch_jobs`, `admin`), services (`JikanClient`, `MediaService`, `BatchWorker`, `BackupService`), and database access via factory patterns. Frontend uses a parameterized Media Showcase Factory (`getMediaConfig`), generic views, and modular component units.

## Project Structure

### Documentation (this feature)

```text
specs/002-amotoa-v3-core/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── accounts.py
│   │   │   ├── media.py
│   │   │   ├── progress.py
│   │   │   ├── batch_jobs.py
│   │   │   └── admin.py
│   │   └── schemas/
│   │       ├── media.py
│   │       ├── progress.py
│   │       └── batch.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── exceptions.py
│   ├── services/
│   │   ├── jikan_client.py
│   │   ├── media_service.py
│   │   ├── progress_service.py
│   │   ├── batch_worker.py
│   │   └── backup_service.py
│   └── main.py
└── tests/
    ├── conftest.py
    ├── test_media_router.py
    ├── test_progress_router.py
    ├── test_jikan_client.py
    └── test_backup_service.py

frontend/
├── src/
│   ├── components/
│   │   ├── AccountSwitcher.tsx
│   │   ├── CustomizationPanel.tsx
│   │   ├── DashboardGrid.tsx
│   │   ├── MediaCard.tsx
│   │   ├── MediaCarousel.tsx
│   │   ├── MediaQuickInfoHover.tsx
│   │   ├── ImageGalleryModal.tsx
│   │   ├── FranchiseRelations.tsx
│   │   ├── FranchiseMoviesList.tsx
│   │   ├── BatchImportModal.tsx
│   │   └── common/
│   │       └── PlaceholderImage.tsx
│   ├── hooks/
│   │   ├── useActiveAccount.ts
│   │   └── useMediaShowcase.ts
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── WIPPage.tsx
│   │   ├── MediaShowcasePage.tsx
│   │   ├── MediaDetailPage.tsx
│   │   └── DailyProgressPage.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── mediaConfig.ts
│   ├── App.tsx
│   ├── index.css
│   └── main.tsx
└── tests/
```

**Structure Decision**: Web application layout separating FastAPI `backend` and Vite React `frontend`, following domain-driven subpackages under `src/services` and `src/api/routers` for the backend, and component/factory modularity under `frontend/src`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. Architecture adheres to all five core principles.
