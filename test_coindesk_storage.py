"""
Test to verify CoinDesk crawler stores full content in database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.crawl_result import CrawlResult
from app.models.crawler_config import CrawlerConfig
from app.services.crawler_service import CrawlerService


async def test_full_content_storage():
    """Test that full content is stored in database"""
    print("Testing CoinDesk Full Content Storage")
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
    
    print("\n1. Crawling CoinDesk (this may take a minute)...")
    result = await crawler_service.crawl_site("coindesk")
    
    print(f"\n   Result:")
    print(f"   - Articles Found: {result.get('articles_found', 0)}")
    print(f"   - Articles Saved: {result.get('articles_saved', 0)}")
    print(f"   - Success: {result.get('success', False)}")
    
    if result.get('success') and result.get('articles_saved', 0) > 0:
        print("\n2. Verifying full content storage...")
        articles = await CrawlResult.find(CrawlResult.source_site == "coindesk").sort(-CrawlResult.crawl_timestamp).limit(5).to_list()
        
        print(f"\n   Checking {len(articles)} most recent articles:")
        for i, article in enumerate(articles, 1):
            content_len = len(article.content) if article.content else 0
            print(f"\n   Article {i}:")
            print(f"   - Title: {article.title[:70] if article.title else 'N/A'}...")
            print(f"   - Content Length: {content_len:,} characters")
            print(f"   - URL: {article.source_url}")
            
            if article.content:
                # Show first and last 100 chars to verify it's full content
                first_part = article.content[:100]
                last_part = article.content[-100:] if len(article.content) > 200 else ""
                print(f"   - First 100 chars: {first_part}...")
                if last_part:
                    print(f"   - Last 100 chars: ...{last_part}")
                
                # Verify it's substantial content
                if content_len > 1000:
                    print(f"   ✓ Full content stored ({content_len:,} chars)")
                else:
                    print(f"   ⚠ Content seems short ({content_len:,} chars)")
    else:
        print(f"\n   No articles were saved. Error: {result.get('error', 'Unknown')}")
    
    client.close()
    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_full_content_storage())


