# Implementation Plan: Main Dashboard & Account Switcher

**Branch**: `001-main-dashboard` | **Date**: 2026-05-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-main-dashboard/spec.md`

## Summary

The objective is to implement a central dashboard with a multi-account switcher and personalization settings. The system will support 12 utility modules (rendered as WIP templates initially). It will handle layout visibility preferences and database isolation (Shared vs Separated) for two default accounts: `car-j works` and `car-j home`.

Our technical approach utilizes a containerized FastAPI backend (Factory Pattern) and a React Vite frontend (Tailwind/Shadcn-inspired aesthetics) deployed via Docker Swarm. MongoDB runs externally on the host system, and data separation is enforced using document filtering keys and header-driven contexts.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.0+ / Node.js 18+ (Frontend)  
**Primary Dependencies**: FastAPI, motor (async MongoDB driver), React, Vite, Tailwind CSS, Lucide React (for premium dashboard icons)  
**Storage**: External MongoDB (accessed via `MONGODB_URI` from `.env`)  
**Testing**: pytest (Backend), vitest (Frontend)  
**Target Platform**: Localhost / Docker Swarm (overlay network)  
**Project Type**: web-service (Backend) + web app (Frontend)  
**Performance Goals**: Switch active account and refresh layout in <200ms; MongoDB CRUD responses in <50ms  
**Constraints**: Fully offline-capable, zero external cloud dependencies, Docker Swarm orchestration, database excluded from compose stack  
**Scale/Scope**: 2 accounts, 12 utilities, 1 database collection for layout config, 1 generic collection per active utility  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Docker Swarm & External DB Gate**: Frontend and Backend must run on Docker Swarm, and MongoDB must be external. **Status**: Passed (Confirmed compose setup will exclude MongoDB, fetching `MONGODB_URI` from environment).
2. **Two-Account Switching Gate**: Switcher must be local and fast, switching between `car-j works` and `car-j home`. **Status**: Passed (Header `X-Active-Account` and Cookie/LocalStorage tracking designed).
3. **Data Isolation Gate**: Layout visibility and data sharing (Shared vs Separated) settings must be respected. **Status**: Passed (MongoDB document schema filters dynamically by active header and sharing mode).
4. **WIP Page Activation Gate**: 12 utilities must exist from Day 1, rendering premium glassmorphic placeholders if unbuilt. **Status**: Passed (Placeholder page component designed).
5. **Factory Pattern Gate**: Code must be structured modularly using App and Route Factories on backend and component modularity on frontend. **Status**: Passed (Factories included in directory blueprints).

## Project Structure

### Documentation (this feature)

```text
specs/001-main-dashboard/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── routers/
│   │   │   ├── accounts.py
│   │   │   └── dashboard.py
│   │   └── server.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   └── main.py
├── Dockerfile
├── requirements.txt
└── tests/

frontend/
├── src/
│   ├── components/
│   │   ├── AccountSwitcher.tsx
│   │   ├── CustomizationPanel.tsx
│   │   ├── DashboardGrid.tsx
│   │   └── WIPPlaceholder.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   └── WIPPage.tsx
│   ├── services/
│   │   └── api.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── Dockerfile
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tests/

docker-compose.yml
.env.example
```

**Structure Decision**: Option 2: Web application. We will separate frontend (React) and backend (FastAPI) into two top-level directories containerized together using Docker Swarm.

## Complexity Tracking

*No violations of constitution detected.*
