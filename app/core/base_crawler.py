"""
Base crawler with support for both RSS and HTML crawling
"""
import aiohttp
import hashlib
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from app.config import settings
import asyncio


class BaseCrawler(ABC):
    """Base class for all crawlers with common async functionality"""
    
    def __init__(self, site_name: str, base_url: str, rss_url: Optional[str] = None):
        self.site_name = site_name
        self.base_url = base_url
        self.rss_url = rss_url
        self.timeout = aiohttp.ClientTimeout(total=settings.CRAWLER_TIMEOUT)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            "User-Agent": settings.CRAWLER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers=headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_url_hash(self, url: str) -> str:
        """Generate a hash for URL to detect duplicates"""
        return hashlib.sha256(url.encode()).hexdigest()
    
    async def fetch(self, url: str, retries: int = None) -> Optional[str]:
        """Fetch content from URL with retry logic"""
        retries = retries or settings.CRAWLER_RETRY_ATTEMPTS
        
        for attempt in range(retries):
            try:
                async with self.session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 404:
                        return None
                    response.raise_for_status()
            except asyncio.TimeoutError:
                if attempt < retries - 1:
                    await asyncio.sleep(settings.CRAWLER_RETRY_DELAY)
                    continue
                raise
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(settings.CRAWLER_RETRY_DELAY)
                    continue
                print(f"Error fetching {url}: {str(e)}")
                raise
        
        return None
    
    async def fetch_json(self, url: str, retries: int = None) -> Optional[Dict]:
        """Fetch JSON content from URL"""
        retries = retries or settings.CRAWLER_RETRY_ATTEMPTS
        
        for attempt in range(retries):
            try:
                async with self.session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    response.raise_for_status()
            except asyncio.TimeoutError:
                if attempt < retries - 1:
                    await asyncio.sleep(settings.CRAWLER_RETRY_DELAY)
                    continue
                raise
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(settings.CRAWLER_RETRY_DELAY)
                    continue
                print(f"Error fetching JSON {url}: {str(e)}")
                raise
        
        return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content"""
        return BeautifulSoup(html, 'lxml')
    
    def parse_xml(self, xml_content: str) -> ET.Element:
        """Parse XML content"""
        return ET.fromstring(xml_content)
    
    # RSS Helper Methods
    
    async def fetch_rss(self) -> Optional[ET.Element]:
        """Fetch and parse RSS feed"""
        if not self.rss_url:
            return None
        
        try:
            content = await self.fetch(self.rss_url)
            if content:
                return self.parse_xml(content)
        except Exception as e:
            print(f"Error fetching RSS from {self.rss_url}: {str(e)}")
        
        return None
    
    def extract_rss_items(self, root: ET.Element) -> List[ET.Element]:
        """Extract all item elements from RSS feed"""
        return root.findall('.//item')
    
    def extract_rss_field(self, item: ET.Element, field: str, 
                         namespace: Optional[str] = None) -> Optional[str]:
        """Extract a field from RSS item"""
        if namespace:
            elem = item.find(f'{namespace}:{field}', self._get_rss_namespaces())
        else:
            elem = item.find(field)
        
        if elem is not None and elem.text:
            return elem.text.strip()
        return None
    
    def _get_rss_namespaces(self) -> dict:
        """Get common RSS namespaces"""
        return {
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'media': 'http://search.yahoo.com/mrss/'
        }
    
    def clean_html_content(self, html_content: str, 
                          unwanted_selectors: Optional[List[str]] = None) -> str:
        """Clean HTML content and extract text"""
        soup = self.parse_html(html_content)
        
        # Default unwanted selectors
        if unwanted_selectors is None:
            unwanted_selectors = [
                'script', 'style', 'nav', 'aside', 'footer', 'header',
                '.ad', '.advertisement', '.social', '.share', 
                'button', '.newsletter', '.related', '.comments'
            ]
        
        # Remove unwanted elements
        for selector in unwanted_selectors:
            for elem in soup.select(selector):
                elem.decompose()
        
        # Extract text from paragraphs and headings
        paragraphs = soup.find_all(['p', 'h2', 'h3', 'h4', 'li', 'blockquote'])
        content_parts = []
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 30:
                content_parts.append(text)
        
        return '\n\n'.join(content_parts) if content_parts else ''
    
    # Abstract Methods
    
    @abstractmethod
    async def get_article_urls(self, limit: int = None) -> List[str]:
        """Extract article URLs from the site - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse individual article and extract data - must be implemented by subclasses"""
        pass
    
    async def crawl(self, limit: int = None) -> List[Dict[str, Any]]:
        """Main crawl method that orchestrates the crawling process"""
        results = []
        
        try:
            article_urls = await self.get_article_urls(limit=limit)
            
            if not article_urls:
                return results
            
            semaphore = asyncio.Semaphore(settings.CRAWLER_MAX_CONCURRENT)
            
            async def crawl_article(url: str):
                async with semaphore:
                    try:
                        article_data = await self.parse_article(url)
                        if article_data:
                            article_data['url_hash'] = self._get_url_hash(url)
                            article_data['source_site'] = self.site_name
                            article_data['source_url'] = url
                            return article_data
                    except Exception as e:
                        print(f"Error crawling article {url}: {str(e)}")
                    return None
            
            tasks = [crawl_article(url) for url in article_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            results = [r for r in results if r and not isinstance(r, Exception)]
            
        except Exception as e:
            print(f"Error in crawl process for {self.site_name}: {str(e)}")
            raise
        
        return results
