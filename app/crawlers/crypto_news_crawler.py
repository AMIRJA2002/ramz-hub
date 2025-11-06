from typing import List, Dict, Optional, Any
from app.core.base_crawler import BaseCrawler
from urllib.parse import urljoin


class CryptoNewsCrawler(BaseCrawler):
    """Generic crawler for crypto news sites"""
    
    def __init__(self, site_name: str, base_url: str):
        super().__init__(site_name=site_name, base_url=base_url)
        self.entry_url = base_url
    
    async def get_article_urls(self) -> List[str]:
        """Extract article URLs using generic selectors"""
        urls = []
        try:
            html = await self.fetch(self.entry_url)
            if not html:
                return urls
            
            soup = self.parse_html(html)
            
            # Generic selectors that work on most news sites
            selectors = [
                'article a',
                '.post a',
                '.article a',
                '.news-item a',
                '.story a',
                'h2 a',
                'h3 a',
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if full_url.startswith(self.base_url) and full_url not in urls:
                            urls.append(full_url)
            
        except Exception as e:
            print(f"Error getting article URLs from {self.site_name}: {str(e)}")
        
        return urls[:20]
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse article using generic selectors"""
        try:
            html = await self.fetch(url)
            if not html:
                return None
            
            soup = self.parse_html(html)
            
            # Try multiple selectors for title
            title = None
            title_selectors = ['h1', '.title', '.post-title', '.article-title', 'article h1']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Try multiple selectors for content
            content = None
            content_selectors = ['article', '.content', '.post-content', '.article-content', '.entry-content', 'main']
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
            
            if not title or not content:
                return None
            
            return {
                'title': title,
                'content': content,
                'meta': {
                    'extracted_at': None,  # Could add timestamp here
                }
            }
            
        except Exception as e:
            print(f"Error parsing article {url}: {str(e)}")
            return None




