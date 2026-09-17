import logging
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_holder = Database()

def get_database():
    return db_holder.db

async def init_db():
    logger.info("Initializing connection to MongoDB...")
    db_holder.client = AsyncIOMotorClient(settings.MONGODB_URI)
    
    # Extract database name from connection string or default to 'amotoa'
    db_name = settings.MONGODB_URI.split("/")[-1]
    if not db_name or "?" in db_name:
        db_name = "amotoa"
        
    db_holder.db = db_holder.client[db_name]
    logger.info(f"Connected to MongoDB database: {db_name}")

    # Seed initial account profiles if they do not exist
    await seed_default_accounts()
    
    # Initialize indexes
    await create_indexes()

async def create_indexes():
    db = db_holder.db
    
    # media collection indexes
    await db["media"].create_index("mal_id", unique=True)
    await db["media"].create_index([("type", 1), ("year", -1)])
    await db["media"].create_index([("type", 1), ("published_status", 1)])
    await db["media"].create_index("franchise_root_id")
    await db["media"].create_index(
        [
            ("title_japanese", "text"),
            ("title_english", "text"),
            ("title_default", "text"),
            ("synopsis", "text")
        ]
    )

    # user_progress collection indexes
    await db["user_progress"].create_index([("account_id", 1), ("media_mal_id", 1)], unique=True)
    await db["user_progress"].create_index([("account_id", 1), ("media_type", 1), ("status", 1)])
    await db["user_progress"].create_index([("account_id", 1), ("is_favorite", 1)])

    # batch_import_jobs collection indexes
    await db["batch_import_jobs"].create_index("job_id", unique=True)
    await db["batch_import_jobs"].create_index("status")

async def close_db():
    if db_holder.client:
        db_holder.client.close()
        logger.info("Closed MongoDB connection")

async def seed_default_accounts():
    accounts_col = db_holder.db["accounts_config"]
    
    default_items = [
        "series", "animes", "youtube", "light_novels", 
        "manga", "jogos", "financas", "saude_fitness", 
        "links", "trabalho", "estudos", "filmes"
    ]
    
    visibility_defaults = {item: True for item in default_items}
    separation_defaults = {item: False for item in default_items}
    
    for account_id in ["car-j-works", "car-j-home"]:
        existing = await accounts_col.find_one({"_id": account_id})
        if not existing:
            logger.info(f"Provisioning initial configuration for profile: {account_id}")
            await accounts_col.insert_one({
                "_id": account_id,
                "visibility_settings": visibility_defaults,
                "data_separation_settings": separation_defaults
            })
