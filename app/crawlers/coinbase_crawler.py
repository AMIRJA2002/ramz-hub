from typing import List, Dict, Optional, Any
from app.core.base_crawler import BaseCrawler
from urllib.parse import urljoin


class CoinbaseCrawler(BaseCrawler):
    """Crawler for Coinbase blog/news"""
    
    def __init__(self, base_url: str = "https://blog.coinbase.com"):
        super().__init__(
            site_name="coinbase",
            base_url=base_url
        )
    
    async def get_article_urls(self) -> List[str]:
        """Extract article URLs from Coinbase blog"""
        urls = []
        try:
            html = await self.fetch(f"{self.base_url}/latest")
            if not html:
                return urls
            
            soup = self.parse_html(html)
            
            # Find article links (adjust selectors based on actual site structure)
            article_links = soup.select('article a, .post-link, .article-link, a[href*="/post/"]')
            
            for link in article_links:
                href = link.get('href', '')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in urls:
                        urls.append(full_url)
            
        except Exception as e:
            print(f"Error getting article URLs from Coinbase: {str(e)}")
        
        return urls[:20]  # Limit to 20 articles per crawl
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse individual Coinbase article"""
        try:
            html = await self.fetch(url)
            if not html:
                return None
            
            soup = self.parse_html(html)
            
            title = soup.select_one('h1, .title, .post-title')
            title_text = title.get_text(strip=True) if title else None
            
            content = soup.select_one('article, .post-content, .article-content, .content')
            content_text = content.get_text(strip=True) if content else None
            
            if not title_text or not content_text:
                return None
            
            return {
                'title': title_text,
                'content': content_text,
                'meta': {
                    'author': self._extract_author(soup),
                    'published_date': self._extract_date(soup),
                    'tags': self._extract_tags(soup),
                }
            }
            
        except Exception as e:
            print(f"Error parsing Coinbase article {url}: {str(e)}")
            return None
    
    def _extract_author(self, soup) -> Optional[str]:
        """Extract author name"""
        author = soup.select_one('.author, [rel="author"], .by-author')
        return author.get_text(strip=True) if author else None
    
    def _extract_date(self, soup) -> Optional[str]:
        """Extract publication date"""
        date = soup.select_one('time, .date, .published-date, [datetime]')
        return date.get('datetime') or (date.get_text(strip=True) if date else None)
    
    def _extract_tags(self, soup) -> List[str]:
        """Extract tags"""
        tags = []
        tag_elements = soup.select('.tags a, .tag, [rel="tag"]')
        for tag in tag_elements:
            tag_text = tag.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)
        return tags
