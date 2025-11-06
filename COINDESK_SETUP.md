# CoinDesk Crawler Setup

## Changes Made

### 1. Base URL Updated
- **Old**: `https://www.coindesk.com`
- **New**: `https://www.coindesk.com/latest-crypto-news`
- The crawler now only checks the latest crypto news page

### 2. Crawler Behavior
- **Regular crawls**: Fetches **all articles from the page** (typically 16-17 articles per page)
- **Import command**: Can fetch and store **300 articles** (or custom amount)
- **Publish Date**: Automatically extracted from article page or URL if not found in page

### 3. Footer/Disclosure Filtering
- Automatically filters out CoinDesk disclosure text:
  - "Disclosure & Policies"
  - "CoinDesk is an award-winning media outlet"
  - "Bullish (NYSE:BLSH)"
  - "equity-based compensation"
  - And other footer content

## Usage

### Regular Crawling (All articles from page)
The crawler will automatically fetch all articles from the latest-crypto-news page (typically 16-17 articles) when scheduled or triggered:

```bash
# Via API
curl -X POST "http://localhost:8000/api/crawler/crawl" \
  -H "Content-Type: application/json" \
  -d '{"site_name": "coindesk"}'

# Or via Python
from app.services.crawler_service import CrawlerService
service = CrawlerService()
result = await service.crawl_site("coindesk")
```

### Import 300 Articles (One-time)
Run the import command to populate the database with 300 latest articles:

```bash
# Import 300 articles (default)
python import_coindesk_articles.py

# Import custom number of articles
python import_coindesk_articles.py 500
```

The import script will:
1. Fetch article URLs from the latest-crypto-news page
2. Parse each article and extract full content
3. Store in database (skipping duplicates)
4. Update the crawler config's last_crawl timestamp

## Configuration

The base URL is configured in:
- `app/crawlers/coindesk_crawler.py` - Default base URL
- `init_crawlers.py` - Database configuration
- Database `CrawlerConfig` - Can be updated via API

To update the base URL in the database:
```bash
curl -X PUT "http://localhost:8000/api/crawler/config/coindesk" \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://www.coindesk.com/latest-crypto-news"}'
```

