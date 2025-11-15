"""
CoinDesk crawler using RSS for article discovery and HTML for content extraction
"""
from typing import List, Dict, Optional, Any
from app.core.base_crawler import BaseCrawler
import xml.etree.ElementTree as ET
import re


class CoindeskCrawler(BaseCrawler):
    """Crawler for CoinDesk news using hybrid RSS + HTML approach"""
    
    RSS_FEED_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    
    def __init__(self, base_url: str = "https://www.coindesk.com/"):
        super().__init__(
            site_name="coindesk",
            base_url=base_url,
            rss_url=self.RSS_FEED_URL
        )
    
    async def get_article_urls(self, limit: int = None) -> List[str]:
        """Extract article URLs from RSS feed"""
        article_urls = []
        
        try:
            root = await self.fetch_rss()
            if not root:
                return article_urls
            
            for item in self.extract_rss_items(root):
                url = self.extract_rss_field(item, 'link')
                if url and self._is_valid_article_url(url):
                    article_urls.append(url)
                    if limit and len(article_urls) >= limit:
                        break
            
        except Exception as e:
            print(f"Error getting article URLs from CoinDesk RSS: {str(e)}")
        
        return article_urls
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse individual CoinDesk article from HTML"""
        try:
            html = await self.fetch(url)
            if not html:
                return None
            
            soup = self.parse_html(html)
            
            # Extract title
            title = self._extract_title(soup)
            if not title:
                return None
            
            # Extract content
            content = self._extract_content(soup)
            if not content or len(content) < 100:
                return None
            
            # Extract metadata
            published_date = self._extract_date(soup, url)
            author = self._extract_author(soup)
            category = self._extract_category(soup, url)
            
            return {
                'title': title,
                'content': content,
                'meta': {
                    'author': author,
                    'published_date': published_date,
                    'category': category,
                }
            }
            
        except Exception as e:
            print(f"Error parsing CoinDesk article {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract article title"""
        title_selectors = [
            'h1.at-headline',
            'h1.headline',
            'h1[class*="headline"]',
            'h1[class*="title"]',
            'article h1',
            'h1',
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 10:
                    return title
        
        return None
    
    def _extract_content(self, soup) -> Optional[str]:
        """Extract article content"""
        # CoinDesk articles have paragraphs directly in the body
        # Find all paragraphs in the page
        all_paragraphs = soup.find_all('p')
        content_parts = []
        
        for p in all_paragraphs:
            text = p.get_text(strip=True)
            # Filter out unwanted text and short paragraphs
            if (text and len(text) > 50 and 
                not self._is_unwanted_text(text)):
                content_parts.append(text)
        
        if content_parts:
            return '\n\n'.join(content_parts)
        
        return None
    
    def _is_unwanted_text(self, text: str) -> bool:
        """Check if text should be filtered out"""
        text_lower = text.lower()
        
        # Filter common unwanted patterns
        unwanted_patterns = [
            'share', 'copy link', 'subscribe', 'newsletter',
            'cookie', 'privacy policy', 'disclosure',
            'coindesk is an award-winning', 'editorial policies'
        ]
        
        if any(pattern in text_lower for pattern in unwanted_patterns):
            return True
        
        # Filter price tickers
        if re.match(r'^\$[\d,]+\.?\d*\s*[\d.%+-]+%?$', text.strip()):
            return True
        
        if re.match(r'^[A-Z]{2,10}\$[\d,]+', text.strip()):
            return True
        
        return False
    
    def _extract_author(self, soup) -> Optional[str]:
        """Extract author name"""
        # Try meta tags first
        meta_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
        ]
        
        for selector in meta_selectors:
            meta_elem = soup.select_one(selector)
            if meta_elem:
                author = meta_elem.get('content')
                if author and len(author.strip()) > 0:
                    return author.strip()
        
        # Try HTML selectors
        author_selectors = [
            '[itemprop="author"]',
            '[rel="author"]',
            '[class*="author"]',
            '[class*="byline"]',
            '.at-authors',
            'a[href*="/author/"]',
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = author_elem.get_text(strip=True)
                # Clean up
                author_text = re.sub(r'^By\s+', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2:
                    return ' '.join(author_text.split())
        
        return None
    
    def _extract_date(self, soup, url: str) -> Optional[str]:
        """Extract publication date"""
        # Try time element first
        time_elem = soup.find('time', attrs={'datetime': True})
        if time_elem:
            return time_elem.get('datetime')
        
        # Try meta tags
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish-date"]',
            'meta[property="og:published_time"]',
        ]
        
        for selector in meta_selectors:
            meta_elem = soup.select_one(selector)
            if meta_elem:
                content = meta_elem.get('content')
                if content:
                    return content
        
        # Extract from URL (CoinDesk URLs have pattern: /2025/11/14/)
        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month}-{day}T00:00:00Z"
        
        return None
    
    def _extract_category(self, soup, url: str) -> Optional[str]:
        """Extract category"""
        # Try to get from URL first
        url_lower = url.lower()
        url_categories = {
            '/markets/': 'Markets',
            '/policy/': 'Policy',
            '/tech/': 'Tech',
            '/business/': 'Finance',
            '/opinion/': 'Opinion',
        }
        
        for pattern, category in url_categories.items():
            if pattern in url_lower:
                return category
        
        # Try meta tags
        meta_elem = soup.select_one('meta[property="article:section"]')
        if meta_elem:
            category = meta_elem.get('content')
            if category:
                return category.strip().title()
        
        # Try HTML selectors
        category_elem = soup.select_one('[class*="category"]')
        if category_elem:
            cat_text = category_elem.get_text(strip=True)
            if cat_text and cat_text.lower() not in ['category', 'section']:
                return cat_text.title()
        
        return None
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        if not url or "coindesk.com" not in url:
            return False
        
        # Exclude non-article pages
        excluded = [
            '/tag/', '/author/', '/category/', '/page/', '/search',
            '/newsletter', '/podcast', '/video/', '/sponsored/',
            '/latest-crypto-news'
        ]
        
        if any(exc in url.lower() for exc in excluded):
            return False
        
        # Check for date pattern (articles have dates in URL)
        if re.search(r'/\d{4}/\d{2}/\d{2}/', url):
            return True
        
        # Check for category paths
        if any(cat in url for cat in ['/markets/', '/policy/', '/tech/', '/business/', '/opinion/']):
            return True
        
        return False
