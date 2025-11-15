"""
CryptoNews.com crawler using RSS feed
Avoids Cloudflare protection by using official RSS feed instead of HTML scraping
"""
from typing import List, Dict, Optional, Any
from app.core.base_crawler import BaseCrawler
import xml.etree.ElementTree as ET


class CryptoNewsCrawler(BaseCrawler):
    """Crawler for CryptoNews.com using RSS feed"""
    
    RSS_FEED_URL = "https://cryptonews.com/feed/"
    
    def __init__(self, base_url: str = "https://cryptonews.com/news/"):
        super().__init__(
            site_name="crypto_news",
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
                    article_urls.append(url)
                    if limit and len(article_urls) >= limit:
                        break
            
        except Exception as e:
            print(f"Error getting article URLs from CryptoNews RSS: {str(e)}")
        
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
            
            # Find the RSS item matching this URL
            for item in self.extract_rss_items(root):
                item_url = self.extract_rss_field(item, 'link')
                if item_url == url:
                    return self._parse_rss_item(item)
            
            return None
            
        except Exception as e:
            print(f"Error parsing CryptoNews article {url}: {str(e)}")
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
        category = self.extract_rss_field(item, 'category')
        
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
        content_elem = item.find('content:encoded', self._get_rss_namespaces())
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
        
        # Filter out boilerplate text specific to CryptoNews
        lines = content.split('\n\n')
        filtered_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if ('appeared first on' not in line_lower and
                'the post' not in line_lower[:20]):
                filtered_lines.append(line)
        
        return '\n\n'.join(filtered_lines)
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        if not url or "cryptonews.com" not in url:
            return False
        
        # Exclude non-article pages
        excluded = ['/tag/', '/author/', '/category/', '/page/', '/search', 
                   '/about', '/contact', '/privacy', '/terms', '/cookie',
                   '/sitemap', '/feed', '/api', '/login', '/register']
        
        return not any(exc in url.lower() for exc in excluded)
