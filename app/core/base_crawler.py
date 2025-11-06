import aiohttp
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from app.config import settings
import asyncio


class BaseCrawler(ABC):
    """Base class for all crawlers with common async functionality"""
    
    def __init__(self, site_name: str, base_url: str):
        self.site_name = site_name
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=settings.CRAWLER_TIMEOUT)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={"User-Agent": settings.CRAWLER_USER_AGENT}
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
        """Fetch HTML content from URL with retry logic"""
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
    
    @abstractmethod
    async def get_article_urls(self) -> List[str]:
        """Extract article URLs from the site - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse individual article and extract data - must be implemented by subclasses"""
        pass
    
    async def crawl(self) -> List[Dict[str, Any]]:
        """Main crawl method that orchestrates the crawling process"""
        results = []
        
        try:
            article_urls = await self.get_article_urls()
            print('crwl', article_urls)
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
