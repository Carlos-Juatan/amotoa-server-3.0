# Feature Specification: Main Dashboard & Account Switcher

**Feature Branch**: `001-main-dashboard`  
**Created**: 2026-05-23  
**Status**: Draft  
**Input**: User description: "Ok, agora vamos fazer o dashboard principal. Ele deve conter os 12 items (series, animes, youtube, light novels, manga, jogos, finanças, saúde e fitness, links, trabalho, estudos, filmes). E o sistema de troca de contas, onde eu posso customizar quais itens vão ser mostrados ou não, e quais itens vão ter conteúdo compartilhado ou separado."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Grid Dashboard Navigation (Priority: P1)

As a user of the Amontoa Server Hub, I want to access a central dashboard displaying 12 core utilities so that I can easily navigate to active services or see a polished placeholder for upcoming features.

**Why this priority**: Core navigation landing page, acting as the entry point for all current and future feature modules.

**Independent Test**: Load the root dashboard route, confirm that all 12 utility cards render correctly with appropriate styling, and verify that clicking active cards navigates to the active module while clicking inactive cards redirects to a styled WIP page.

**Acceptance Scenarios**:

1. **Given** the user navigates to the homepage, **When** the page loads, **Then** a responsive, glassmorphic grid of 12 items is shown with distinct icons/labels (series, animes, youtube, light novels, manga, jogos, finanças, saúde e fitness, links, trabalho, estudos, filmes).
2. **Given** a utility card represents an unimplemented feature (WIP), **When** the user clicks the card, **Then** the system displays a premium glassmorphic Work In Progress placeholder page.

---

### User Story 2 - Account Switcher (Priority: P1)

As a user of the Hub, I want to toggle between different accounts without authentication barriers so that I can instantly switch between my personal and professional contexts.

**Why this priority**: Required to toggle database context and layout configurations dynamically, serving as the basis for profile separation.

**Independent Test**: Switch accounts using the switcher widget on the dashboard, and verify that the local and backend context (API headers) changes instantly.

**Acceptance Scenarios**:

1. **Given** the user is on the dashboard, **When** they click the account switcher, **Then** they see the list of accounts (e.g. 'car-j works' and 'car-j home').
2. **Given** the user selects a new active account, **When** the dashboard updates, **Then** the active account state changes in localStorage/session, subsequent API calls transmit the active account ID in the request header, and the UI layout refreshes to reflect that account's specific visibility settings.

---

### User Story 3 - Customization Panel (Priority: P2)

As a user, I want to customize which of the 12 utilities are visible on my active dashboard and toggle their content sharing status (shared vs separated).

**Why this priority**: Provides the personalization and data isolation toggle controls requested by the user.

**Independent Test**: Open the customization panel, toggle visibility and content sharing for a specific item, and verify that dashboard layout and data queries reflect the updated visibility and isolation modes immediately.

**Acceptance Scenarios**:

1. **Given** the user is on the dashboard, **When** they open the Customization Panel, **Then** they see a configuration list for all 12 items with toggle controls for Visibility (Show/Hide) and Data Separation (Shared/Separated).
2. **Given** the user sets 'youtube' visibility to Hidden for 'car-j works', **When** 'car-j works' is the active account, **Then** the YouTube card is hidden from the dashboard grid.
3. **Given** the user switches back to 'car-j home', **When** the dashboard loads, **Then** the YouTube card is visible (independent configurations).

---

### User Story 4 - Data Separation & Merge Transition (Priority: P2)

As a user, I want to manage how existing data behaves when changing sharing modes (Shared vs Separated) so that I do not lose data or mix contexts unintentionally.

**Why this priority**: Directly implements the user's specific guidelines on data inheritance and merging during layout reconfiguration.

**Independent Test**: Perform transition actions (Shared -> Separated, Separated -> Shared) for a test category, and verify database assignment and frontend rendering matches expectations.

**Acceptance Scenarios**:

1. **Given** the user changes a utility's state from Shared to Separated, **When** they submit the changes, **Then** the system MUST display a prompt asking which account ('car-j works' or 'car-j home') will retain the existing data.
2. **Given** the user selects 'car-j works' to retain the existing data, **When** the transition is completed, **Then** all existing records are assigned to 'car-j works' (visible only under 'car-j works' profile), and 'car-j home' starts with zero records.
3. **Given** both 'car-j works' and 'car-j home' have private records for a separated utility, **When** the user changes that utility to Shared, **Then** all private records for both accounts are merged (made visible under both profiles).

---

### Edge Cases

- **Toggling Content Separation mid-session**: If a user switches an item from "Shared" to "Separated" while viewing the item page, the page data must refresh instantly to filter based on the new isolation mode.
- **Empty Active Account Header**: If the frontend fails to supply the active account header to the backend, the backend should default to a safe fallback (e.g., 'car-j home') or return a validation error.
- **Hiding All Items**: If the user sets all 12 items to hidden for an account, the dashboard should display a user-friendly message indicating the dashboard is empty and prompt them to open settings.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST render a responsive dashboard layout containing up to 12 items: series, animes, youtube, light novels, manga, jogos, finanças, saúde e fitness, links, trabalho, estudos, filmes.
- **FR-002**: The system MUST provide an account switcher component on the dashboard to allow changing the active account.
- **FR-003**: The system MUST support account-specific layout visibility configurations stored in the database.
- **FR-004**: The system MUST support account-specific data isolation settings (Shared vs Separated) for each of the 12 items.
- **FR-005**: The backend MUST dynamically filter queries based on the active account and the item's sharing configuration (Shared = query all items without account restriction; Separated = query items matching the active account's ID or with null/unset owner depending on rules).
- **FR-006**: The system MUST support two pre-configured accounts: `car-j works` and `car-j home`.
- **FR-007**: When toggling an item from Shared to Separated, the system MUST prompt the user to select which account inherits the existing content, while the other account starts with empty content.
- **FR-008**: When toggling an item from Separated to Shared, the system MUST automatically merge the data from both accounts, making it visible to both profiles.

### Key Entities *(include if feature involves data)*

- **AccountConfiguration**:
  - Represents the settings for an account profile.
  - Attributes:
    - `accountId` (string, unique key e.g., 'car-j-works', 'car-j-home')
    - `visibilitySettings` (map of item ID to boolean indicating shown/hidden)
    - `dataSeparationSettings` (map of item ID to boolean indicating whether data is shared or separated)
- **GenericItem (representing content across utilities)**:
  - Represents individual content records (e.g., a bookmark link, a finance entry, a game log).
  - Attributes:
    - `contentId` (string)
    - `itemType` (string matching one of the 12 categories)
    - `accountId` (string, optional - present only if created under "Separated" mode for a specific account)
    - `data` (object/map containing category-specific fields)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Switching accounts on the dashboard updates the visible grid items in less than 200ms.
- **SC-002**: Customization settings (visibility and sharing toggle) are persisted in the database, with save confirmation feedback under 500ms.
- **SC-003**: The system ensures 100% data separation for items configured as "Separated", preventing data tagged with 'car-j-works' from appearing when 'car-j-home' is active.
- **SC-004**: Unimplemented items successfully display the premium Work In Progress screen within 100ms when clicked.

## Assumptions

- The app is designed for local development on Docker Swarm/localhost, and does not require credentials/passwords for account switching.
- Standard accounts 'car-j works' and 'car-j home' are preloaded or created automatically upon database initialization.
- MongoDB is running externally on the host system as specified in the Hub Constitution.
