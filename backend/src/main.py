import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.database import init_db, close_db
from src.api.routers.accounts import router as accounts_router

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
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
    yield
    # Shutdown: Close database connection
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

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": settings.PROJECT_NAME}

    return app

app = create_app()
