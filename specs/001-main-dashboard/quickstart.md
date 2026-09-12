# Quickstart: Main Dashboard & Account Switcher

This guide outlines steps to build, run, and test the Main Dashboard and Account Switcher locally in the development environment.

---

## Prerequisites

1. **MongoDB**: Ensure a MongoDB instance is running locally on your host machine.
2. **Environment Variables**: Create a `.env` file in the project root containing:
   ```env
   MONGODB_URI=mongodb://localhost:27017
   ```
3. **Docker**: Ensure Docker is installed and running, and Docker Swarm is initialized:
   ```bash
   docker swarm init
   ```

---

## Running the Application

### 1. Build and Start Services
Deploy the Swarm stack using:
```bash
docker stack deploy -c docker-compose.yml amontoa
```

### 2. Verify Database Initialization
The FastAPI backend service automatically checks if default configurations exist for `car-j-works` and `car-j-home` profiles in the `accounts_config` collection. If not, it provisions them with all 12 items visible and sharing modes disabled.

---

## Verifying the Flow (Testing)

### 1. Root Dashboard Landing
Navigate to `http://localhost:3000` (or the mapped frontend port).
- You should see the custom dashboard grid showing all 12 utilities: series, animes, youtube, light novels, manga, jogos, finanças, saúde e fitness, links, trabalho, estudos, filmes.
- Unimplemented utilities should load a dark, glassmorphic "Work in Progress" screen when clicked.

### 2. Switch Accounts
- Use the selector at the top to toggle between **car-j works** and **car-j home**.
- Open your browser's Developer Tools (Network tab) and verify that all outgoing requests contain the header:
  `X-Active-Account: car-j-works` or `X-Active-Account: car-j-home`.

### 3. Customize Visibility & Sharing
- Open the Customization Panel.
- Toggle visibility of a utility (e.g. `youtube` -> Hidden) for the active account. Save and confirm it vanishes from the grid.
- Switch to the other profile and confirm the utility remains visible.
- Toggle data isolation for a utility (e.g. `links` -> Separated) and verify the prompts requesting which account retains the existing shared data.
