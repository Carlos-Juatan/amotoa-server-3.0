# Amontoa Server Hub

A personal utility hub with 12 modules, per-account dashboard customization, and data isolation controls. Built with FastAPI + React Vite, deployed via Docker Swarm. MongoDB runs externally on the host.

## Requirements

- Docker (Swarm mode enabled)
- MongoDB running on the host machine

## Setup

```bash
# 1. Clone and enter the project
cd amotoa-server-3.0

# 2. Copy and edit environment variables
cp .env.example .env
# Edit .env: set MONGODB_URI to your host MongoDB address

# 3. Initialize Docker Swarm (if not already active)
docker swarm init

# 4. Build images
docker build -t amontoa-backend:latest ./backend
docker build -t amontoa-frontend:latest ./frontend

# 5. Deploy the stack
docker stack deploy -c docker-compose.yml amontoa
```

## Access

| Service  | URL                     |
|----------|-------------------------|
| Frontend | http://localhost:3000   |
| Backend  | http://localhost:8000   |
| API Docs | http://localhost:8000/docs |

## Development (local, no Docker)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev   # runs on http://localhost:3000 (or Vite default port)
```

## Environment Variables

| Variable        | Description                                   | Default                         |
|-----------------|-----------------------------------------------|---------------------------------|
| `MONGODB_URI`   | MongoDB connection string (external host)     | `mongodb://localhost:27017/amotoa` |
| `BACKEND_PORT`  | Host port mapped to the backend container     | `8000`                          |
| `FRONTEND_PORT` | Host port mapped to the frontend container    | `3000`                          |
| `VITE_API_URL`  | URL the browser uses to reach the backend API | `http://localhost:8000`         |

## Features

- **12-module dashboard grid** with glassmorphic cards
- **Account switcher** — toggle between `car-j works` and `car-j home` with no auth walls
- **Customization panel** — show/hide modules per account
- **Data isolation** — toggle Shared / Separated per module:
  - Shared → Separated: choose which account inherits existing data
  - Separated → Shared: records from both accounts are merged automatically
- **WIP placeholder** — unimplemented modules show a premium "in development" screen

## Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python 3.11 · FastAPI · Motor     |
| Frontend | React 19 · Vite · Tailwind CSS    |
| Database | MongoDB (external)                |
| Infra    | Docker Swarm · overlay network    |
