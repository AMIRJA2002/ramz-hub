"""
Cointelegraph.com crawler using RSS feed
"""
from typing import List, Dict, Optional, Any
from app.core.base_crawler import BaseCrawler
import xml.etree.ElementTree as ET
import re


class CointelegraphCrawler(BaseCrawler):
    """Crawler for Cointelegraph.com using RSS feed"""
    
    RSS_FEED_URL = "https://cointelegraph.com/feed"
    
    def __init__(self, base_url: str = "https://cointelegraph.com"):
        super().__init__(
            site_name="cointelegraph",
            base_url=base_url,
            rss_url=self.RSS_FEED_URL
        )
        # Cache RSS feed to avoid multiple fetches
        self._rss_cache = None
    
    async def get_article_urls(self, limit: int = None) -> List[str]:
        """Extract article URLs from RSS feed"""
        article_urls = []
        
        try:
            root = await self._get_rss_feed()
            if not root:
                return article_urls
            
            for item in self.extract_rss_items(root):
                url = self.extract_rss_field(item, 'link')
                if url and self._is_valid_article_url(url):
                    # Clean URL from query parameters
                    clean_url = url.split('?')[0]
                    article_urls.append(clean_url)
                    if limit and len(article_urls) >= limit:
                        break
            
        except Exception as e:
            print(f"Error getting article URLs from Cointelegraph RSS: {str(e)}")
        
        return article_urls
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse article from RSS feed cache
        Since RSS has full content, we extract it from the cached feed
        """
        try:
            root = await self._get_rss_feed()
            if not root:
                return None
            
            # Find the RSS item matching this URL (clean URL for comparison)
            clean_url = url.split('?')[0]
            for item in self.extract_rss_items(root):
                item_url = self.extract_rss_field(item, 'link')
                if item_url:
                    item_clean_url = item_url.split('?')[0]
                    if item_clean_url == clean_url:
                        return self._parse_rss_item(item)
            
            return None
            
        except Exception as e:
            print(f"Error parsing Cointelegraph article {url}: {str(e)}")
            return None
    
    async def _get_rss_feed(self) -> Optional[ET.Element]:
        """Get RSS feed with caching to avoid multiple fetches"""
        if self._rss_cache is None:
            self._rss_cache = await self.fetch_rss()
        return self._rss_cache
    
    def _parse_rss_item(self, item: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a single RSS item into article data"""
        
        # Extract URL
        url = self.extract_rss_field(item, 'link')
        if not url or not self._is_valid_article_url(url):
            return None
        
        # Extract title
        title = self.extract_rss_field(item, 'title')
        if not title:
            return None
        
        # Extract content
        content = self._extract_content(item)
        if not content or len(content) < 100:
            return None
        
        # Extract metadata
        author = self.extract_rss_field(item, 'creator', 'dc')
        published_date = self.extract_rss_field(item, 'pubDate')
        category = self._extract_category(item)
        
        return {
            'title': title,
            'content': content,
            'meta': {
                'author': author,
                'published_date': published_date,
                'category': category,
            }
        }
    
    def _extract_content(self, item: ET.Element) -> Optional[str]:
        """Extract article content from RSS item"""
        
        # Try content:encoded first (full article content)
        namespaces = self._get_rss_namespaces()
        content_elem = item.find('content:encoded', namespaces)
        if content_elem is not None and content_elem.text:
            return self._clean_content(content_elem.text)
        
        # Fallback to description
        desc = self.extract_rss_field(item, 'description')
        if desc:
            return self._clean_content(desc)
        
        return None
    
    def _clean_content(self, html_content: str) -> str:
        """Clean HTML content and extract text"""
        content = self.clean_html_content(html_content)
        
        # Filter out boilerplate text specific to Cointelegraph
        lines = content.split('\n\n')
        filtered_lines = []
        
        for line in lines:
            line_lower = line.lower()
            # Filter out unwanted patterns
            if ('read more' not in line_lower and
                'appeared first on' not in line_lower and
                'the post' not in line_lower[:20] and
                'subscribe' not in line_lower and
                'newsletter' not in line_lower):
                filtered_lines.append(line)
        
        return '\n\n'.join(filtered_lines)
    
    def _extract_category(self, item: ET.Element) -> Optional[str]:
        """Extract category from RSS item"""
        # Try to get first category
        categories = item.findall('category')
        if categories:
            # Get the first non-empty category
            for cat in categories:
                if cat.text and cat.text.strip():
                    return cat.text.strip()
        
        return None
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        if not url or "cointelegraph.com" not in url:
            return False
        
        # Exclude non-article pages
        excluded = [
            '/tag/', '/author/', '/category/', '/page/', '/search',
            '/about', '/contact', '/privacy', '/terms', '/cookie',
            '/sitemap', '/feed', '/api', '/login', '/register',
            '/newsletter', '/podcast', '/video/', '/sponsored/',
            '/magazine/'
        ]
        
        url_lower = url.lower()
        if any(exc in url_lower for exc in excluded):
            return False
        
        # Include article URLs (they usually have date pattern or specific paths)
        # Cointelegraph articles can be in various formats:
        # - /news/...
        # - /magazine/...
        # - /price/...
        # - Date pattern: /2025/12/...
        if re.search(r'/(news|magazine|price)/', url_lower) or \
           re.search(r'/\d{4}/\d{2}/', url_lower):
            return True
        
        return False

