"""
Script to initialize crawler configurations in the database
Run this once to set up the default crawler configurations
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.crawler_config import CrawlerConfig
from app.models.crawl_result import CrawlResult


async def init_crawler_configs():
    """Initialize default crawler configurations"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.MONGODB_DB_NAME]
    
    # Initialize Beanie
    await init_beanie(
        database=database,
        document_models=[CrawlResult, CrawlerConfig]
    )
    
    # Create unique index for site_name
    try:
        await CrawlerConfig.get_motor_collection().create_index(
            [("site_name", 1)], unique=True
        )
    except Exception:
        pass  # Index might already exist
    
    # Default crawler configurations
    crawler_configs = [
        {
            "site_name": "coinbase",
            "base_url": "https://blog.coinbase.com",
            "is_active": True,
            "crawl_interval_minutes": 15,
            "config": {
                "description": "Coinbase blog and news",
                "type": "registered"
            }
        },
        {
            "site_name": "coindesk",
            "base_url": "https://www.coindesk.com/latest-crypto-news",
            "is_active": True,
            "crawl_interval_minutes": 15,
            "config": {
                "description": "CoinDesk cryptocurrency news",
                "type": "registered"
            }
        },
        {
            "site_name": "crypto_news",
            "base_url": "https://cryptonews.com/news/",
            "is_active": True,
            "crawl_interval_minutes": 30,
            "config": {
                "description": "CryptoNews.com news crawler (RSS-based)",
                "type": "generic"
            }
        }
    ]
    
    print("Initializing crawler configurations...")
    
    for config_data in crawler_configs:
        site_name = config_data["site_name"]
        
        # Check if config already exists
        existing = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
        
        if existing:
            print(f"✓ Config for '{site_name}' already exists, skipping...")
        else:
            # Create new config
            crawler_config = CrawlerConfig(**config_data)
            await crawler_config.insert()
            print(f"✓ Created config for '{site_name}' - {config_data['base_url']}")
    
    print("\n✅ Crawler configurations initialized successfully!")
    print("\nActive crawlers:")
    active_configs = await CrawlerConfig.find(CrawlerConfig.is_active == True).to_list()
    for config in active_configs:
        print(f"  - {config.site_name}: {config.base_url} (every {config.crawl_interval_minutes} min)")
    
    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(init_crawler_configs())

