from typing import List, Dict, Optional, Any
from app.core.base_crawler import BaseCrawler
from urllib.parse import urljoin, urlparse
import re


class CoindeskCrawler(BaseCrawler):
    """Crawler for CoinDesk news"""
    
    def __init__(self, base_url: str = "https://www.coindesk.com/latest-crypto-news"):
        super().__init__(
            site_name="coindesk",
            base_url=base_url
        )
    
    async def get_article_urls(self, limit: int = None) -> List[str]:
        """Extract article URLs from CoinDesk latest news page
        
        Args:
            limit: Maximum number of articles to return (None = get all from page)
        """
        urls = []
        try:
            # Only check the latest-crypto-news page
            html = await self.fetch(self.base_url)
            if html:
                soup = self.parse_html(html)
                urls.extend(self._extract_urls_from_page(soup))
            
            # Remove duplicates and filter valid article URLs
            unique_urls = list(set(urls))
            article_urls = [url for url in unique_urls if self._is_valid_article_url(url)]
            
        except Exception as e:
            print(f"Error getting article URLs from CoinDesk: {str(e)}")
        
        # If limit is specified, apply it; otherwise return all found articles
        if limit:
            return article_urls[:limit]
        return article_urls
    
    def _extract_urls_from_page(self, soup) -> List[str]:
        """Extract article URLs from a page"""
        urls = []
        seen = set()
        
        # CoinDesk uses various selectors for article links
        # For latest-crypto-news page, we need more comprehensive selectors
        selectors = [
            'a[href*="/202"]',  # Articles with year in URL (e.g., /2025/11/06/)
            'article a[href*="/"]',
            '.article-card a',
            '.card a',
            '.headline a',
            'h2 a',
            'h3 a',
            '[data-module="ArticleCard"] a',
            '[class*="article"] a',
            '[class*="story"] a',
            '[class*="Card"] a',  # CoinDesk card components
            'a[href*="/markets/"]',
            'a[href*="/policy/"]',
            'a[href*="/tech/"]',
            'a[href*="/business/"]',
            'a[href*="/opinion/"]',
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if href:
                    # Make absolute URL
                    full_url = urljoin("https://www.coindesk.com", href)
                    # Only add if it's from coindesk.com, looks like an article, and we haven't seen it
                    if ("coindesk.com" in full_url and 
                        full_url not in seen and
                        self._is_valid_article_url(full_url)):
                        urls.append(full_url)
                        seen.add(full_url)
        
        return urls
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL"""
        # CoinDesk article URLs must be from coindesk.com
        if not url or "coindesk.com" not in url:
            return False
        
        # Exclude non-article pages
        excluded = ['/tag/', '/author/', '/category/', '/page/', '/search', '/newsletter', '/podcast', '/latest-crypto-news', '/video/', '/sponsored/']
        if any(exc in url for exc in excluded):
            return False
        
        # Article URLs usually have date pattern like /2024/01/15/ or /2025/11/06/
        date_pattern = r'/\d{4}/\d{2}/\d{2}/'
        if re.search(date_pattern, url):
            return True
        
        # Or have article-like structure
        if '/markets/' in url or '/policy/' in url or '/tech/' in url or '/business/' in url or '/opinion/' in url:
            return True
        
        return False
    
    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse individual CoinDesk article"""
        try:
            html = await self.fetch(url)
            if not html:
                return None
            
            soup = self.parse_html(html)
            
            # Extract title - CoinDesk uses various selectors
            title = None
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
                    break
            
            # Extract content - CoinDesk article body
            content = None
            content_selectors = [
                'div[class*="article-body"]',
                'div[class*="articleBody"]',
                'div[class*="ArticleBody"]',
                'div[class*="content"]',
                'article div[class*="body"]',
                '[data-module="ArticleBody"]',
                'div.at-article-body',
                'div[data-module="ArticleBody"]',
                'div.article-body',
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove unwanted elements (ads, social buttons, price tickers, footer, etc.)
                    for unwanted in content_elem.select('script, style, nav, aside, .ad, .social, .share, button, .newsletter, .related, .comments, footer, header, [class*="price"], [class*="ticker"], [class*="crypto-price"], [id*="price"], [data-module*="Price"], [class*="disclosure"], [class*="footer"], [id*="disclosure"], [id*="footer"]'):
                        unwanted.decompose()
                    
                    # Get ALL paragraphs and divs with text - NO LIMITS
                    paragraphs = content_elem.find_all(['p', 'div', 'h2', 'h3', 'h4', 'li', 'blockquote'])
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        # Filter out very short text, social media text, navigation, price data, and footer/disclosure text
                        if (text and len(text) > 30 and 
                            'share' not in text.lower() and 
                            'copy link' not in text.lower() and
                            'subscribe' not in text.lower() and
                            'newsletter' not in text.lower() and
                            'cookie' not in text.lower() and
                            'privacy policy' not in text.lower() and
                            not re.match(r'^\$[\d,]+\.?\d*\s*[\d.%+-]+%?$', text.strip()) and  # Filter price tickers
                            not re.match(r'^[A-Z]{2,10}\$[\d,]+', text.strip()) and  # Filter crypto price formats
                            not self._is_footer_text(text)):  # Filter footer/disclosure text
                            content_parts.append(text)
                    
                    if content_parts and len('\n\n'.join(content_parts)) > 200:
                        content = '\n\n'.join(content_parts)  # NO LIMIT - full content
                        break
            
            # If no structured content found, try getting all paragraphs from article tag
            if not content or len(content) < 200:
                article_elem = soup.find('article')
                if article_elem:
                    # Remove unwanted elements
                    for unwanted in article_elem.select('script, style, nav, aside, .ad, .social, .share, button, header, footer, .related, .comments, .newsletter, [class*="price"], [class*="ticker"], [data-module*="Price"], [class*="disclosure"], [class*="footer"], [id*="disclosure"], [id*="footer"]'):
                        unwanted.decompose()
                    
                    # Get ALL paragraphs - NO LIMITS
                    paragraphs = article_elem.find_all(['p', 'div', 'h2', 'h3', 'h4', 'li', 'blockquote'])
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if (text and len(text) > 50 and 
                            'share' not in text.lower() and 
                            'copy link' not in text.lower() and
                            'subscribe' not in text.lower() and
                            'newsletter' not in text.lower() and
                            not re.match(r'^\$[\d,]+\.?\d*\s*[\d.%+-]+%?$', text.strip()) and  # Filter price tickers
                            not re.match(r'^[A-Z]{2,10}\$[\d,]+', text.strip()) and  # Filter crypto price formats
                            not self._is_footer_text(text)):  # Filter footer/disclosure text
                            content_parts.append(text)
                    if content_parts:
                        content = '\n\n'.join(content_parts)  # NO LIMIT - full content
            
            # Last resort: get all paragraphs from body
            if not content or len(content) < 200:
                # Remove unwanted sections first
                for unwanted in soup.select('script, style, nav, aside, .ad, .social, .share, button, header, footer, .related, .comments, .newsletter, .sidebar, [class*="price"], [class*="ticker"], [data-module*="Price"]'):
                    unwanted.decompose()
                
                paragraphs = soup.find_all(['p', 'div', 'h2', 'h3'])
                content_parts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    # Stronger filtering for last resort
                    if (text and len(text) > 100 and 
                        'share' not in text.lower() and 
                        'subscribe' not in text.lower() and
                        'newsletter' not in text.lower() and
                        'cookie' not in text.lower() and
                        'privacy' not in text.lower() and
                        not re.match(r'^\$[\d,]+\.?\d*\s*[\d.%+-]+%?$', text.strip()) and  # Filter price tickers
                        not re.match(r'^[A-Z]{2,10}\$[\d,]+', text.strip()) and  # Filter crypto price formats
                        not self._is_footer_text(text)):  # Filter footer/disclosure text
                        content_parts.append(text)
                if content_parts:
                    content = '\n\n'.join(content_parts)  # NO LIMIT - full content
            
            if not title:
                return None
            
            # Ensure we have meaningful content
            if not content or len(content.strip()) < 100:
                return None
            
            # Extract metadata
            published_date = self._extract_date(soup)
            
            # If date not found in page, try to extract from URL
            # CoinDesk URLs have pattern: /2025/11/06/article-title
            if not published_date:
                date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
                if date_match:
                    year, month, day = date_match.groups()
                    # Create ISO date string (assume midnight UTC if no time available)
                    published_date = f"{year}-{month}-{day}T00:00:00Z"
            
            meta = {
                "author": self._extract_author(soup),
                "published_date": published_date,
                "category": self._extract_category(soup, url),
            }
            
            # Return full content - no truncation
            return {
                'title': title,
                'content': content.strip(),  # Full content, just strip whitespace
                'meta': meta,
            }
            
        except Exception as e:
            print(f"Error parsing CoinDesk article {url}: {str(e)}")
            return None
    
    def _extract_author(self, soup) -> Optional[str]:
        """Extract author name"""
        # Try meta tags first (most reliable)
        meta_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            'meta[property="og:article:author"]',
        ]
        for selector in meta_selectors:
            meta_elem = soup.select_one(selector)
            if meta_elem:
                author = meta_elem.get('content')
                if author and len(author.strip()) > 0:
                    return author.strip()
        
        # Try JSON-LD structured data
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for author
                    if 'author' in data:
                        author_data = data['author']
                        if isinstance(author_data, dict):
                            if 'name' in author_data:
                                return author_data['name']
                        elif isinstance(author_data, str):
                            return author_data
                    # Check if it's an array
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'author' in item:
                                author_data = item['author']
                                if isinstance(author_data, dict) and 'name' in author_data:
                                    return author_data['name']
                                elif isinstance(author_data, str):
                                    return author_data
            except:
                pass
        
        # Try HTML selectors
        author_selectors = [
            '[itemprop="author"]',
            '[itemprop="author"] [itemprop="name"]',
            '[rel="author"]',
            '[class*="author"]',
            '[class*="byline"]',
            '[data-module="Author"]',
            '.at-authors',
            'span[class*="author"]',
            'a[class*="author"]',
            '[data-testid="author"]',
            'a[href*="/author/"]',
        ]
        
        for selector in author_selectors:
            author_elems = soup.select(selector)
            for author_elem in author_elems:
                # Try itemprop content first
                if author_elem.get('itemprop') == 'author':
                    name_elem = author_elem.find(attrs={'itemprop': 'name'})
                    if name_elem:
                        author_text = name_elem.get_text(strip=True)
                    else:
                        author_text = author_elem.get('content') or author_elem.get_text(strip=True)
                else:
                    author_text = author_elem.get_text(strip=True)
                
                # Clean up author text (remove "By" prefix, etc.)
                author_text = re.sub(r'^By\s+', '', author_text, flags=re.IGNORECASE)
                author_text = re.sub(r'^By:\s*', '', author_text, flags=re.IGNORECASE)
                author_text = re.sub(r'^\s*Written by\s+', '', author_text, flags=re.IGNORECASE)
                
                # Filter out very short or common words
                if author_text and len(author_text) > 2 and author_text.lower() not in ['by', 'author', 'written', 'staff']:
                    # Remove extra whitespace
                    author_text = ' '.join(author_text.split())
                    return author_text
        
        return None
    
    def _extract_date(self, soup) -> Optional[str]:
        """Extract publication date"""
        # Try time element with datetime attribute first (most reliable)
        time_elems = soup.find_all('time')
        for time_elem in time_elems:
            # Check datetime attribute
            datetime_attr = time_elem.get('datetime')
            if datetime_attr:
                return datetime_attr
            # Check pubdate attribute
            pubdate = time_elem.get('pubdate')
            if pubdate:
                return pubdate
        
        # Try meta tags for publish date (common in news sites)
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish-date"]',
            'meta[name="pubdate"]',
            'meta[name="date"]',
            'meta[property="og:published_time"]',
            'meta[name="DC.date"]',
            'meta[name="sailthru.date"]',
        ]
        for selector in meta_selectors:
            meta_elem = soup.select_one(selector)
            if meta_elem:
                content = meta_elem.get('content')
                if content:
                    return content
        
        # Try JSON-LD structured data
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for datePublished
                    if 'datePublished' in data:
                        return data['datePublished']
                    # Check if it's an array
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'datePublished' in item:
                                return item['datePublished']
            except:
                pass
        
        # Try various date selectors in HTML
        date_selectors = [
            'time[datetime]',
            '[class*="date"]',
            '[class*="timestamp"]',
            '[class*="published"]',
            '[class*="publish"]',
            '[class*="publish-date"]',
            '[class*="pub-date"]',
            '[data-module="Date"]',
            '.at-timestamp',
            '[data-testid="date"]',
            '[data-testid="timestamp"]',
            '[itemprop="datePublished"]',
        ]
        
        for selector in date_selectors:
            date_elems = soup.select(selector)
            for date_elem in date_elems:
                # Try datetime attribute first
                datetime_attr = date_elem.get('datetime')
                if datetime_attr:
                    return datetime_attr
                # Try itemprop content
                if date_elem.get('itemprop') == 'datePublished':
                    content = date_elem.get('content')
                    if content:
                        return content
                # Try data attributes
                for attr in ['data-date', 'data-timestamp', 'data-published', 'data-publish-date']:
                    if date_elem.get(attr):
                        return date_elem.get(attr)
                # Otherwise get text and try to parse
                date_text = date_elem.get_text(strip=True)
                if date_text and len(date_text) > 5:
                    # Try to extract ISO date format from text
                    iso_match = re.search(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}', date_text)
                    if iso_match:
                        return iso_match.group(0)
                    return date_text
        
        # Last resort: try to extract from URL (CoinDesk URLs have date pattern)
        # This is done in parse_article, but we can also check here
        return None
    
    def _is_footer_text(self, text: str) -> bool:
        """Check if text is footer/disclosure text that should be filtered out"""
        text_lower = text.lower()
        
        # Check for disclosure/footer patterns
        footer_keywords = [
            'disclosure & policies',
            'disclosure and policies',
            'coindesk is an award-winning',
            'editorial policies',
            'editorial independence',
            'freedom from bias',
            'bullish (nyse:',
            'equity-based compensation',
            'digital asset platform',
            'market infrastructure',
            'institutionally focused',
            'abide by a strict',
            'adopted a set of principles',
        ]
        
        # If text contains multiple footer keywords, it's likely footer text
        matches = sum(1 for keyword in footer_keywords if keyword in text_lower)
        if matches >= 2:
            return True
        
        # Check for specific long disclosure text pattern
        if 'coindesk is an award-winning media outlet' in text_lower:
            return True
        if 'coindesk is part of bullish' in text_lower:
            return True
        if 'coindesk employees, including journalists, may receive' in text_lower:
            return True
        
        return False
    
    def _extract_category(self, soup, url: str) -> Optional[str]:
        """Extract category"""
        # Try to get from URL first (most reliable for CoinDesk)
        url_lower = url.lower()
        if '/markets/' in url_lower:
            return 'Markets'
        elif '/policy/' in url_lower:
            return 'Policy'
        elif '/tech/' in url_lower:
            return 'Tech'
        elif '/business/' in url_lower:
            return 'Business'
        elif '/opinion/' in url_lower:
            return 'Opinion'
        elif '/coindesk-indices/' in url_lower or '/indices/' in url_lower:
            return 'Indices'
        elif '/press-release/' in url_lower:
            return 'Press Release'
        elif '/finance/' in url_lower:
            return 'Finance'
        elif '/video/' in url_lower:
            return 'Video'
        elif '/podcast/' in url_lower:
            return 'Podcast'
        
        # Try meta tags
        meta_selectors = [
            'meta[property="article:section"]',
            'meta[name="category"]',
            'meta[property="og:article:section"]',
        ]
        for selector in meta_selectors:
            meta_elem = soup.select_one(selector)
            if meta_elem:
                category = meta_elem.get('content')
                if category and len(category.strip()) > 0:
                    # Capitalize first letter
                    return category.strip().title()
        
        # Try JSON-LD structured data
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for articleSection
                    if 'articleSection' in data:
                        return data['articleSection'].title()
                    # Check if it's an array
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'articleSection' in item:
                                return item['articleSection'].title()
            except:
                pass
        
        # Try to extract from page HTML
        category_selectors = [
            '[class*="category"]',
            '[class*="section"]',
            '[class*="topic"]',
            '[class*="tag"]',
            '[data-module="Category"]',
            '[itemprop="articleSection"]',
            'a[href*="/tag/"]',
            'a[href*="/category/"]',
        ]
        
        for selector in category_selectors:
            cat_elems = soup.select(selector)
            for cat_elem in cat_elems:
                cat_text = cat_elem.get_text(strip=True)
                # Filter out common non-category text
                if (cat_text and len(cat_text) > 0 and 
                    cat_text.lower() not in ['category', 'section', 'tag', 'tags', 'more', 'read more']):
                    return cat_text.title()
        
        # Last resort: try to infer from URL path
        # Extract first path segment after domain
        path_match = re.search(r'coindesk\.com/([^/]+)/', url)
        if path_match:
            path_segment = path_match.group(1)
            if path_segment and path_segment not in ['www', 'latest-crypto-news', 'tag', 'author', 'search']:
                return path_segment.replace('-', ' ').title()
        
        return None
