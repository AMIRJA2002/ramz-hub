"""
Migrate/Create crawler configurations
Run this to populate the database with crawler configs
"""
import asyncio
from app.database import connect_to_mongo
from app.models.crawler_config import CrawlerConfig

async def migrate_crawlers():
    """Create initial crawler configurations"""
    await connect_to_mongo()
    print("✓ Connected to MongoDB")
    
    # Define crawler configurations
    crawlers = [
        {
            "site_name": "coindesk",
            "base_url": "https://www.coindesk.com",
            "is_active": True,
            "crawl_interval_minutes": 15,
            "config": {
                "description": "CoinDesk - Leading cryptocurrency news"
            }
        },
        {
            "site_name": "crypto_news",
            "base_url": "https://cryptonews.com",
            "is_active": True,
            "crawl_interval_minutes": 15,
            "config": {
                "description": "CryptoNews - Cryptocurrency news and analysis"
            }
        },
        {
            "site_name": "coinbase",
            "base_url": "https://www.coinbase.com/blog",
            "is_active": False,
            "crawl_interval_minutes": 30,
            "config": {
                "description": "Coinbase Blog - Official Coinbase updates"
            }
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for crawler_data in crawlers:
        # Check if already exists
        existing = await CrawlerConfig.find_one(
            CrawlerConfig.site_name == crawler_data["site_name"]
        )
        
        if existing:
            print(f"⊘ Skipped {crawler_data['site_name']} (already exists)")
            skipped_count += 1
            continue
        
        # Create new config
        config = CrawlerConfig(**crawler_data)
        await config.insert()
        print(f"✓ Created {crawler_data['site_name']}")
        created_count += 1
    
    print(f"\n{'='*50}")
    print(f"Migration complete!")
    print(f"Created: {created_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Total: {created_count + skipped_count}")
    print(f"{'='*50}\n")
    
    # List all configs
    all_configs = await CrawlerConfig.find_all().to_list()
    print("Current crawler configurations:")
    for config in all_configs:
        status = "🟢 Active" if config.is_active else "🔴 Inactive"
        print(f"  {status} {config.site_name} - Every {config.crawl_interval_minutes} minutes")

if __name__ == "__main__":
    asyncio.run(migrate_crawlers())
