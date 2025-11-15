"""
Test script for CoinDesk crawler
"""
import asyncio
from app.crawlers.coindesk_crawler import CoindeskCrawler


async def test_coindesk():
    """Test the CoinDesk crawler"""
    print("=" * 60)
    print("Testing CoinDesk Crawler (RSS + HTML)")
    print("=" * 60)
    
    async with CoindeskCrawler() as crawler:
        # Test getting article URLs from RSS
        print("\n1. Testing get_article_urls() from RSS...")
        article_urls = await crawler.get_article_urls(limit=5)
        print(f"   Found {len(article_urls)} article URLs from RSS feed")
        
        if not article_urls:
            print("   ❌ No article URLs found!")
            return
        
        for i, url in enumerate(article_urls[:3], 1):
            print(f"   {i}. {url[:70]}...")
        
        # Test parsing individual article
        print("\n2. Testing parse_article() on first URL...")
        first_url = article_urls[0]
        article = await crawler.parse_article(first_url)
        
        if article:
            print(f"   ✓ Successfully parsed article:")
            print(f"     Title: {article['title'][:60]}...")
            print(f"     Content: {len(article['content'])} chars")
            print(f"     Author: {article['meta'].get('author', 'N/A')}")
            print(f"     Date: {article['meta'].get('published_date', 'N/A')}")
            print(f"     Category: {article['meta'].get('category', 'N/A')}")
        else:
            print(f"   ❌ Failed to parse article")
            return
        
        # Test full crawl
        print("\n3. Testing full crawl() method...")
        articles = await crawler.crawl(limit=3)
        print(f"   Retrieved {len(articles)} full articles\n")
        
        if not articles:
            print("   ❌ No articles retrieved!")
            return
        
        # Display article details
        for i, article in enumerate(articles, 1):
            print(f"   Article {i}:")
            print(f"     Title: {article['title'][:60]}...")
            print(f"     Content: {len(article['content'])} chars")
            print(f"     Author: {article['meta'].get('author', 'N/A')}")
            print(f"     Date: {article['meta'].get('published_date', 'N/A')}")
            print(f"     Category: {article['meta'].get('category', 'N/A')}")
            print()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_coindesk())
