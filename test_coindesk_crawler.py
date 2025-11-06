"""
Test script for CoinDesk crawler
Run this to verify the crawler is working correctly
"""
import asyncio
from app.crawlers.coindesk_crawler import CoindeskCrawler


async def test_coindesk_crawler():
    """Test the CoinDesk crawler"""
    print("Testing CoinDesk Crawler...")
    print("=" * 50)
    
    crawler = CoindeskCrawler()
    
    async with crawler:
        # Test getting article URLs
        print("\n1. Testing get_article_urls()...")
        article_urls = await crawler.get_article_urls()
        print(f"   Found {len(article_urls)} article URLs")
        
        if article_urls:
            print(f"\n   First 5 URLs:")
            for i, url in enumerate(article_urls[:5], 1):
                print(f"   {i}. {url}")
            
            # Test parsing first article
            print(f"\n2. Testing parse_article() on first URL...")
            first_url = article_urls[0]
            print(f"   URL: {first_url}")
            
            article_data = await crawler.parse_article(first_url)
            
            if article_data:
                print(f"\n   ✓ Successfully parsed article!")
                print(f"   Title: {article_data.get('title', 'N/A')[:100]}")
                print(f"   Content length: {len(article_data.get('content', ''))} characters")
                print(f"   Author: {article_data.get('meta', {}).get('author', 'N/A')}")
                print(f"   Date: {article_data.get('meta', {}).get('published_date', 'N/A')}")
                print(f"   Category: {article_data.get('meta', {}).get('category', 'N/A')}")
                
                # Show first 200 chars of content
                content = article_data.get('content', '')
                if content:
                    print(f"\n   Content preview:")
                    print(f"   {content[:200]}...")
            else:
                print(f"   ✗ Failed to parse article")
        else:
            print("   ✗ No article URLs found")
        
        # Test full crawl
        print(f"\n3. Testing full crawl()...")
        results = await crawler.crawl()
        print(f"   Crawled {len(results)} articles")
        
        if results:
            print(f"\n   Sample results:")
            for i, result in enumerate(results[:3], 1):
                print(f"\n   Article {i}:")
                print(f"   - Title: {result.get('title', 'N/A')[:80]}")
                print(f"   - URL: {result.get('source_url', 'N/A')}")
                print(f"   - Content: {len(result.get('content', ''))} chars")
    
    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_coindesk_crawler())


