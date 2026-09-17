# Quickstart Guide: Plataforma Pessoal de Gestão de Mídias (Amontoa V3.0)

**Feature Branch**: `002-amotoa-v3-core`  
**Date**: 2026-09-17  

---

## 1. Prerequisites

- **Python**: 3.11+ (virtual environment recommended)
- **Node.js**: 20+ & npm 10+
- **MongoDB**: External instance running on localhost (default: `mongodb://localhost:27017/amotoa`)
- **Docker & Docker Swarm**: Configured if running via container stack

---

## 2. Environment Configuration

Ensure your `.env` file in the repository root contains:

```env
PROJECT_NAME="Amontoa Server Hub"
MONGODB_URI="mongodb://localhost:27017/amotoa"
BACKUP_DIR="./backups"
MANGA_LN_SYNC_INTERVAL="weekly"
JIKAN_API_URL="https://api.jikan.moe/v4"
```

---

## 3. Running Locally (Development Mode)

### 3.1 Backend Service

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run FastAPI development server on port 8000
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Verify backend health:
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"Amontoa Server Hub"}
```

### 3.2 Frontend Service

```bash
cd frontend
npm install

# Run Vite dev server on port 3000 (or default 5173)
npm run dev
```

Open browser at: `http://localhost:3000` (or `http://localhost:5173`)

---

## 4. Feature Verification & Workflows

### 4.1 Vitrines (Showcases)
1. In the Dashboard (`/`), click on **Animes**, **Mangás**, or **Light Novels**.
2. Observe navigation to `/animes`, `/manga`, or `/light_novels`.
3. Carrousels render categorized by tracking status:
   - "Em andamento"
   - "Favoritos"
   - "Pausados"
   - "Todos os títulos"
4. Observe **Japanese Title** displayed prominently in bold, and **English Title** underneath in a smaller, secondary font.
5. Hover over a cover card to inspect quick details popup (score, episodes/chapters, status).

### 4.2 Search & External Jikan Import
1. In the top search bar, type a title (e.g. `Frieren` or `Sousou no Frieren`).
2. If the item is already in local database, local results display instantly.
3. If not found locally, click **"Buscar na Jikan API"**.
4. Upstream results display with cover, Japanese and English titles.
5. Click **"Importar para o Catálogo"** to ingest into local MongoDB.

### 4.3 Detail Page & Unified Franchise
1. Click on a media card to open `/animes/:id`.
2. Inspect the unified seasons block (grouped by Jikan `Sequel`/`Prequel` relations).
3. Browse official artwork in the horizontal carousel and click to open the full-screen modal.
4. If the media type is **Anime**, verify the **Filmes da Franquia** block is visible and allows toggling watched status.
5. If the media type is **Mangá** or **Light Novel**, verify the Franchise Movies block is completely hidden.

### 4.4 Daily Progress Module
1. Navigate to the progress tracker sub-page: `/{type}/progress` (e.g. `/animes/progress`).
2. Only ongoing media appears (current season airing for Anime; status `Publishing` for Manga/LN).
3. Test quick increment by clicking **`+1`**.
4. Test exact selector dropdown (observe that values beyond `total_units` are disabled/prevented).
5. Click the external streaming/reading link to confirm it opens in a new tab (`target="_blank"`).

### 4.5 Batch Import of Previous Years
1. Open the batch import panel from the top bar.
2. Select type (e.g. `Anime`), year range `2006` to `2008`.
3. Click **"Iniciar Importação em Lote"**.
4. Notice discrete progress updates and error logs in case of Jikan upstream rate limit retries.
5. Click **"Pausar"** and then **"Retomar"** to verify checkpoint resumption.

---

## 5. Automated Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend lint & build validation
cd frontend
npm run lint
npm run build
```
