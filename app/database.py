from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.crawl_result import CrawlResult
from app.models.crawler_config import CrawlerConfig
from app.models.crawl_log import CrawlLog


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def get_database():
    """Get database connection"""
    return db.client[settings.MONGODB_DB_NAME]


async def connect_to_mongo():
    """Create database connection"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = db.client[settings.MONGODB_DB_NAME]
    await init_beanie(
        database=database,
        document_models=[CrawlResult, CrawlerConfig, CrawlLog]
    )
    
    # Create unique index for site_name
    try:
        await CrawlerConfig.get_motor_collection().create_index(
            [("site_name", 1)], unique=True
        )
    except Exception:
        pass  # Index might already exist


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
