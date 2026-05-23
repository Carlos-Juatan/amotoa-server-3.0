# Tasks: Main Dashboard & Account Switcher

**Input**: Design documents from `/specs/001-main-dashboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/accounts.md

**Tests**: Manual validation is planned as per story specifications. Automated tests are not explicitly requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Root config: `docker-compose.yml`, `.env.example`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create root compose structure. File: `docker-compose.yml`
- [ ] T002 Create root environment template. File: `.env.example`
- [ ] T003 [P] Configure backend Python project requirements. File: `backend/requirements.txt`
- [ ] T004 [P] Initialize React Vite template with Tailwind and Lucide. File: `frontend/package.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core server and client infrastructure that MUST be complete before user stories can start.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Setup core backend configuration class using Pydantic Settings. File: `backend/src/core/config.py`
- [ ] T006 Setup MongoDB database connection client factory using Motor. File: `backend/src/core/database.py`
- [ ] T007 Implement FastAPI server factory and root app initialization. File: `backend/src/main.py`
- [ ] T008 [P] Define API request dependency to extract active account from `X-Active-Account` header. File: `backend/src/api/dependencies.py`
- [ ] T009 Setup baseline Tailwind styling and colors for dark developer theme. File: `frontend/src/index.css`
- [ ] T010 Create API client instance utilizing Axios with account header interceptor. File: `frontend/src/services/api.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Grid Dashboard Navigation (Priority: P1) 🎯 MVP

**Goal**: Deliver the primary grid showing all 12 cards, with unimplemented utilities routing to a premium Work in Progress screen.

**Independent Test**: Load the root dashboard route, click any card, and confirm navigation to active pages or the WIP screen.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Create the styled glassmorphic WIP placeholder component. File: `frontend/src/components/WIPPlaceholder.tsx`
- [ ] T012 [P] [US1] Create the page component for WIP routes. File: `frontend/src/pages/WIPPage.tsx`
- [ ] T013 [US1] Create the dashboard layout grid rendering the 12 cards with appropriate icons. File: `frontend/src/components/DashboardGrid.tsx`
- [ ] T014 [US1] Set up Vite React Router paths for dashboard and placeholder sub-pages. File: `frontend/src/App.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Account Switcher (Priority: P1)

**Goal**: Allow quick toggle between `car-j works` and `car-j home` contexts, updating request headers dynamically.

**Independent Test**: Select profile, check network tabs to confirm `X-Active-Account` header updates.

### Implementation for User Story 2

- [ ] T015 [US2] Create the account switcher selector widget in the dashboard header. File: `frontend/src/components/AccountSwitcher.tsx`
- [ ] T016 [US2] Store active account state in localStorage and update API service client. File: `frontend/src/services/api.ts`
- [ ] T017 [US2] Integrate the switcher component into the root application page header. File: `frontend/src/App.tsx`

**Checkpoint**: At this point, switching accounts updates local context and endpoint headers.

---

## Phase 5: User Story 3 - Customization Panel (Priority: P2)

**Goal**: Toggle dashboard card visibility and sharing mode per profile.

**Independent Test**: Toggle visibility on layout, verify dashboard hides card only for current account.

### Implementation for User Story 3

- [ ] T018 [P] [US3] Create the Pydantic schemas for account settings. File: `backend/src/api/routers/accounts.py`
- [ ] T019 [US3] Implement DB CRUD methods to get/update settings in `accounts_config` collection. File: `backend/src/api/routers/accounts.py`
- [ ] T020 [US3] Register the accounts controller router in main server factory. File: `backend/src/main.py`
- [ ] T021 [US3] Build the Customization Panel configuration dialog UI in React. File: `frontend/src/components/CustomizationPanel.tsx`
- [ ] T022 [US3] Bind Customization Panel settings updates with backend API and local dashboard layout state. File: `frontend/src/pages/Dashboard.tsx`

**Checkpoint**: Users can customize cards shown on their screen, persisting choices to DB.

---

## Phase 6: User Story 4 - Data Separation & Merge Transition (Priority: P2)

**Goal**: Manage inheritance of data when toggling isolation (prompt for ownership on split; merge on join).

**Independent Test**: Transition a utility to separated, pick owner, verify other account is empty. Transition back to shared, verify data is unified.

### Implementation for User Story 4

- [ ] T023 [US4] Implement database migration queries in configuration update endpoint. File: `backend/src/api/routers/accounts.py`
- [ ] T024 [US4] Add custom transition configuration prompt/dialog to visibility toggle screen. File: `frontend/src/components/CustomizationPanel.tsx`

**Checkpoint**: Data isolation settings dynamically migrate existing document structures seamlessly.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: General refinements, documentation, and end-to-end user validation.

- [ ] T025 [P] Document Docker Swarm stack deploying steps. File: `README.md`
- [ ] T026 Verify all scenarios and data transition behaviors using quickstart guide. File: `specs/001-main-dashboard/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can run immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 completion. Blocks all User Stories.
- **User Stories (Phases 3 to 6)**: Depend on Phase 2 completion. 
  - US1 (Phase 3) must be complete to display dashboard navigation.
  - US2, US3, and US4 can follow sequentially or in parallel.
- **Polish (Phase 7)**: Depends on completion of all stories.

### Parallel Opportunities

- **Setup**: `T003` and `T004` can be performed in parallel.
- **Foundational**: `T008` (backend dependencies) and `T009`/`T010` (frontend styling and API client setup) can run in parallel.
- **User Story 1**: UI structures `T011` and `T012` can be created in parallel.
- **User Story 3**: Pydantic schema backend setup `T018` and customization components `T021` can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch components in parallel:
Task: "Create the styled glassmorphic WIP placeholder component. File: frontend/src/components/WIPPlaceholder.tsx"
Task: "Create the page component for WIP routes. File: frontend/src/pages/WIPPage.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational blocks.
2. Complete User Story 1.
3. Validate grid loading and WIP redirection on local environment.

### Incremental Delivery

1. Setup + Foundation: Baseline services.
2. User Story 1: Grid Dashboard (Ready for show-and-tell).
3. User Story 2: Account Switcher (Prepares header filters).
4. User Story 3 & 4: Personalization + Data migrations.
