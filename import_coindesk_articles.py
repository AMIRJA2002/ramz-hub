"""
Command to import 300 latest CoinDesk articles into the database
Run this once to populate the database with recent articles
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.crawl_result import CrawlResult
from app.models.crawler_config import CrawlerConfig
from app.crawlers.coindesk_crawler import CoindeskCrawler
from app.services.crawler_service import CrawlerService
import hashlib


async def import_coindesk_articles(count: int = 300):
    """Import specified number of latest CoinDesk articles"""
    print(f"Importing {count} latest CoinDesk articles...")
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
    
    crawler = CoindeskCrawler()
    
    async with crawler:
        print("\n1. Fetching article URLs from latest-crypto-news page...")
        # Fetch all available URLs from the latest-crypto-news page
        # The page may have many articles, so we'll fetch a large batch
        article_urls = await crawler.get_article_urls(limit=count * 2)  # Get more than needed to account for filtering
        print(f"   Found {len(article_urls)} article URLs")
        
        # Limit to requested count
        article_urls = article_urls[:count]
        print(f"   Using {len(article_urls)} URLs for import")
        
        if not article_urls:
            print("   ✗ No articles found!")
            client.close()
            return
        
        print(f"\n2. Parsing and storing articles (target: {count})...")
        saved_count = 0
        skipped_count = 0
        error_count = 0
        
        # Process articles in batches
        batch_size = 20
        for i in range(0, len(article_urls), batch_size):
            batch = article_urls[i:i + batch_size]
            print(f"   Processing batch {i//batch_size + 1} ({len(batch)} articles)...")
            
            for url in batch:
                if saved_count >= count:
                    print(f"\n   ✓ Reached target of {count} articles!")
                    break
                
                try:
                    # Check if article already exists
                    url_hash = hashlib.sha256(url.encode()).hexdigest()
                    existing = await CrawlResult.find_one(CrawlResult.url_hash == url_hash)
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Parse article
                    article_data = await crawler.parse_article(url)
                    
                    if article_data:
                        # Create crawl result
                        crawl_result = CrawlResult(
                            source_url=url,
                            title=article_data.get('title'),
                            content=article_data.get('content'),
                            meta=article_data.get('meta', {}),
                            source_site="coindesk",
                            url_hash=url_hash,
                        )
                        
                        await crawl_result.insert()
                        saved_count += 1
                        
                        if saved_count % 10 == 0:
                            print(f"   ✓ Saved {saved_count} articles so far...")
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    print(f"   ✗ Error processing {url}: {str(e)}")
            
            if saved_count >= count:
                break
        
        print(f"\n3. Import Summary:")
        print(f"   - Articles Saved: {saved_count}")
        print(f"   - Articles Skipped (duplicates): {skipped_count}")
        print(f"   - Errors: {error_count}")
        print(f"   - Total Processed: {saved_count + skipped_count + error_count}")
        
        # Update crawler config last_crawl
        config = await CrawlerConfig.find_one(CrawlerConfig.site_name == "coindesk")
        if config:
            from datetime import datetime, timezone
            config.last_crawl = datetime.now(timezone.utc)
            await config.save()
            print(f"\n   ✓ Updated crawler config last_crawl timestamp")
    
    client.close()
    print("\n" + "=" * 60)
    print("Import completed!")


if __name__ == "__main__":
    import sys
    
    # Allow custom count via command line argument
    count = 300
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"Invalid count argument: {sys.argv[1]}. Using default: 300")
    
    asyncio.run(import_coindesk_articles(count))

