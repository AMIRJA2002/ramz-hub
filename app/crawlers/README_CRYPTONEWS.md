# CryptoNews Crawler

## Quick Start

```python
from app.crawlers.crypto_news_crawler import CryptoNewsCrawler

async with CryptoNewsCrawler() as crawler:
    # Get latest articles
    articles = await crawler.crawl(limit=10)
    
    # Or just get URLs
    urls = await crawler.get_article_urls(limit=5)
```

## How It Works

This crawler uses the CryptoNews.com RSS feed instead of HTML scraping:

1. **Fetch RSS feed** from `https://cryptonews.com/feed/`
2. **Parse XML** to extract article items
3. **Extract content** from `<content:encoded>` field
4. **Clean HTML** and extract text
5. **Return structured data** with title, content, and metadata

## Why RSS?

- ✅ Avoids Cloudflare bot protection
- ✅ Gets 10-20 articles in one request
- ✅ Full article content included
- ✅ Structured metadata (author, date, category)
- ✅ No CSS selectors to maintain

## Data Structure

Each article returns:
```python
{
    'title': str,           # Article title
    'content': str,         # Full article text (3000-5000 chars)
    'meta': {
        'author': str,      # Author name
        'published_date': str,  # ISO date string
        'category': str     # Article category
    },
    'url_hash': str,        # SHA256 hash of URL
    'source_site': str,     # "crypto_news"
    'source_url': str       # Full article URL
}
```

## Testing

```bash
# Run tests
python test_cryptonews_crawler.py

# Verify functionality
python verify_cryptonews_fix.py
```

## Configuration

Default configuration in `init_crawlers.py`:
- **Site name**: `crypto_news`
- **Base URL**: `https://cryptonews.com/news/`
- **Active**: `True`
- **Interval**: 30 minutes

## Notes

- RSS feed updates every 15-30 minutes
- Typically contains 10-20 most recent articles
- No authentication or API key required
- No rate limiting observed
