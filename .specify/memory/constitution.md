<!--
SYNC IMPACT REPORT:
- Version change: 1.2.0 -> 1.3.0
- List of modified principles:
  - PRINCIPLE V: 'Modular Factory Pattern & MongoDB Architecture' -> 'Strict Modularity & Factory Pattern Architecture (Backend & Frontend)'. Formally mandated modular code organization and comprehensive Factory Pattern implementation across both backend (app factories, router factories, service/database client factories) and frontend (component factories, dynamic module/page loaders, service client factories), separating database partitioning details into Technical Architecture and Storage Design.
- Added sections: None
- Removed sections: None
- Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ verified/aligned
  - .specify/templates/spec-template.md: ✅ verified/aligned
  - .specify/templates/tasks-template.md: ✅ verified/aligned
- Follow-up TODOs: None
-->

# Amontoa Server Hub Constitution

## Core Principles

### I. Localhost & Docker Swarm-First (Self-Contained)
The application is a personal offline-first developer hub built to run exclusively on localhost. The backend (Python FastAPI) and frontend (Vite React) services must be fully containerized and orchestrated via Docker Swarm. The MongoDB database must not be defined in docker-compose.yml as it is already running externally on the host system, and it must be accessed via the MONGODB_URI environment variable defined in the .env file. Deploying the swarm stack must require only a single, simple command: 'docker stack deploy -c docker-compose.yml amontoa' for frontend and backend services, with zero external cloud dependencies or complex manual configurations.

### II. Multi-Account Dynamic Isolation
The hub supports two primary accounts, 'car-j works' and 'car-j home', without a password-based authentication wall. Instead, a lightweight local account switcher must be accessible exclusively on the Hub (Home Page). Each account has two customizable configuration dimensions per page/utility: (a) Visibility (completely hide or show a page for a specific account) and (b) Data Isolation (shared data vs separate per-account data). This separation must be enforced at the database and UI routing levels to guarantee a seamless personal-to-work context switch.

### III. Premium Developer-Centric Aesthetics (Tailwind + Shadcn)
Aesthetics are a first-class requirement. The user interface must deliver a sleek, modern developer-hub feel with dark mode styling, curated harmonized palettes (avoiding raw or standard colors), glassmorphism, responsive grids, and subtle micro-animations for hover states and transitions. Default browser controls are forbidden; the interface must leverage the premium aesthetic of Tailwind CSS and Shadcn UI component standards.

### IV. Incremental WIP Activation (Single-Page MVP)
To support phased development, the twelve designated pages (series, animes, youtube, light novels, manga, jogos, finanças, saúde e fitness, links, trabalho, estudos, filmes) are added progressively. Unimplemented pages must render a visually appealing, premium "Work in Progress" (WIP) placeholder page. This approach ensures that the navigation grid is complete and stunning from Day 1, while allowing individual features to be built and activated independently one by one.

### V. Strict Modularity & Factory Pattern Architecture (Backend & Frontend)
Both the backend and frontend codebases MUST be strictly modular and structured around the Factory Pattern as their core architectural foundation.
- **Backend Modularity & Factories**: The backend MUST isolate functionality into decoupled domain modules (`core`, `api/routers`, `services`). Monolithic app instantiation and global state initialization with side-effects are strictly forbidden. The application MUST use application factories (`create_app()`), router factories, and service/database connection factories to initialize, configure, and inject dependencies dynamically.
- **Frontend Modularity & Factories**: The frontend MUST organize code into self-contained, modular feature units (components, pages, services, hooks). Direct monolithic rendering and tightly coupled UI-service bindings are prohibited. Dynamic feature modules, page loaders, and reusable UI structures MUST leverage factory patterns (e.g., dynamic page factories, component/card factories, API client factories) to instantiate view and logic layers based on routing and configuration metadata.
- **Rationale**: Strict modularity coupled with factory patterns enforces clean dependency injection, simplifies isolated unit/integration testing, eliminates hidden side-effects, and enables seamless independent activation of the 12 hub utilities without risk of cross-module regressions.

## Technical Architecture and Storage Design
The system consists of two containerized services working together over a Docker Swarm overlay network, plus an external MongoDB database:
- **Frontend**: A React Vite application with TypeScript, Tailwind CSS, and Shadcn UI. Organized modularly using component and container factories (e.g., dynamic page and card factories). Manages local state for the active account ('car-j works' vs 'car-j home') via localStorage or Cookies. Transmits the active account identifier to the backend via headers (e.g., 'X-Active-Account').
- **Backend**: A Python FastAPI application structured modularly using the Factory Pattern for app initialization (`create_app()`), router registration, and service initialization. Dynamically checks header context for user account information. Connects to the external MongoDB instance using the MONGODB_URI environment variable from .env to fetch page visibility configurations and page contents.
- **Database**: An external MongoDB database instance (running on the host machine, accessed via MONGODB_URI) storing configurations and utility data. A primary 'accounts_config' collection tracks page visibility (boolean map) and sharing toggle state (boolean map) for both accounts. Other collections (like 'links') contain documents that optionally partition data by 'account_id' (e.g., 'car-j-works', 'car-j-home') or omit the field for shared data, dynamic filtering of records being based on active local account headers.

## Development Workflow and Step-by-Step Implementation Strategy
Development proceeds iteratively according to the following gates:
1. **Environment Orchestration**: Implement the Docker Swarm stack setup (via compose/stack files for frontend and backend) and ensure clean communication between services on overlay network, connecting to the external MongoDB instance via MONGODB_URI.
2. **Backend & Database Initialization**: Setup baseline FastAPI app structure using App and Service Factories, modular database client factories connecting to external MongoDB via MONGODB_URI, and configuration collections.
3. **Frontend Hub & Customization Interface**: Design the dynamic homepage hub displaying a beautifully styled grid of the 12 utilities, account switcher, and a configuration panel to adjust visibility/sharing settings.
4. **WIP Page Shells**: Setup Vite routing using page/component factories for all 12 utilities, rendering a polished, high-fidelity glassmorphic 'Work in Progress' placeholder.
5. **Feature Activation (Step-by-Step)**: Replace WIP placeholders with real utility pages, beginning with core requested items like 'links' (which will handle separate content for 'car-j works' and 'car-j home').

## Governance
- The Amontoa Server Hub Constitution governs all development rules, architectural decisions, and repository patterns.
- Changing core paradigms (e.g., introducing a database other than MongoDB, requiring login credentials, or altering the list of 12 pages) requires amending this document first.
- The constitution follows semantic versioning:
  - MAJOR version bumps indicate significant architectural shifts (e.g. database migrations or login requirements).
  - MINOR version bumps denote adding new utility modules, changing orchestration (e.g., Swarm) or core structural patterns (e.g., Factory Pattern).
  - PATCH version bumps cover stylistic and grammatical refinements or typos.
- Review compliance of all features against these principles during planning and code implementation. Use README.md for runtime development guidance.

**Version**: 1.3.0 | **Ratified**: 2026-05-17 | **Last Amended**: 2026-09-15
