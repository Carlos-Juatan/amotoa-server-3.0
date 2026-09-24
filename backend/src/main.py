import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.database import init_db, close_db, get_database
from src.core.scheduler import start_scheduler, stop_scheduler
from src.api.routers.accounts import router as accounts_router
from src.api.routers.media import router as media_router
from src.api.routers.progress import router as progress_router
from src.api.routers.batch_jobs import router as batch_jobs_router
from src.api.routers.admin import router as admin_router

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Establish database client connection
    try:
        await init_db()
        # Start background sync schedulers once the DB is ready
        db = get_database()
        await start_scheduler(db)
    except Exception as e:
        logger.error(f"Failed during startup: {e}")
    yield
    # Shutdown: Cancel schedulers, then close database connection
    await stop_scheduler()
    await close_db()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        lifespan=lifespan
    )

    # Enable CORS for local Vite development server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for dev simplicity
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(accounts_router)
    app.include_router(progress_router)
    app.include_router(media_router)
    app.include_router(batch_jobs_router)
    app.include_router(admin_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": settings.PROJECT_NAME}

    return app

app = create_app()
