"""
Full test of CoinDesk crawler with database storage
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.crawl_result import CrawlResult
from app.models.crawler_config import CrawlerConfig
from app.services.crawler_service import CrawlerService


async def test_full_flow():
    """Test the full crawler flow with database"""
    print("Testing CoinDesk Crawler - Full Flow with Database")
    print("=" * 60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.MONGODB_DB_NAME]
    
    # Initialize Beanie
    await init_beanie(
        database=database,
        document_models=[CrawlResult, CrawlerConfig]
    )
    
    # Create unique index
    try:
        await CrawlerConfig.get_motor_collection().create_index(
            [("site_name", 1)], unique=True
        )
    except Exception:
        pass
    
    # Test the crawler service
    crawler_service = CrawlerService()
    
    print("\n1. Testing crawl_site() for CoinDesk...")
    result = await crawler_service.crawl_site("coindesk")
    
    print(f"\n   Result:")
    print(f"   - Site: {result.get('site_name')}")
    print(f"   - Articles Found: {result.get('articles_found', 0)}")
    print(f"   - Articles Saved: {result.get('articles_saved', 0)}")
    print(f"   - Articles Skipped: {result.get('articles_skipped', 0)}")
    print(f"   - Success: {result.get('success', False)}")
    
    if result.get('success'):
        print("\n2. Checking saved articles in database...")
        articles = await CrawlResult.find(CrawlResult.source_site == "coindesk").sort(-CrawlResult.crawl_timestamp).limit(5).to_list()
        
        print(f"\n   Found {len(articles)} recent articles:")
        for i, article in enumerate(articles, 1):
            print(f"\n   Article {i}:")
            print(f"   - Title: {article.title[:80] if article.title else 'N/A'}")
            print(f"   - URL: {article.source_url}")
            print(f"   - Content: {len(article.content) if article.content else 0} characters")
            print(f"   - Crawled: {article.crawl_timestamp}")
            if article.meta:
                print(f"   - Author: {article.meta.get('author', 'N/A')}")
                print(f"   - Date: {article.meta.get('published_date', 'N/A')}")
                print(f"   - Category: {article.meta.get('category', 'N/A')}")
    else:
        print(f"\n   Error: {result.get('error', 'Unknown error')}")
    
    client.close()
    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_full_flow())


