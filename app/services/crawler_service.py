from typing import List, Dict, Any, Optional
from app.models.crawl_result import CrawlResult
from app.models.crawler_config import CrawlerConfig
from app.models.crawl_log import CrawlLog
from app.crawlers import CoinbaseCrawler, CoindeskCrawler, CryptoNewsCrawler, CointelegraphCrawler
from app.core.base_crawler import BaseCrawler
import datetime
import time


class CrawlerService:
    """Service for managing crawlers and storing results"""
    
    # Track active crawls (in-memory)
    _active_crawls: Dict[str, datetime.datetime] = {}
    
    CRAWLER_REGISTRY = {
        "coinbase": CoinbaseCrawler,
        "coindesk": CoindeskCrawler,
        "crypto_news": CryptoNewsCrawler,
        "cointelegraph": CointelegraphCrawler,
    }
    
    @staticmethod
    async def get_crawler(site_name: str, base_url: Optional[str] = None) -> BaseCrawler:
        """Get crawler instance for a site"""
        # If base_url not provided, try to get it from config
        if not base_url:
            config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
            if config:
                base_url = config.base_url
        
        if site_name in CrawlerService.CRAWLER_REGISTRY:
            return CrawlerService.CRAWLER_REGISTRY[site_name](base_url=base_url)
        else:
            raise ValueError(f"No crawler found for site: {site_name}")
    
    async def crawl_site(self, site_name: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Crawl a specific site and store results"""
        # Mark crawl as active
        start_time = datetime.datetime.now(datetime.timezone.utc)
        CrawlerService._active_crawls[site_name] = start_time
        
        # Create crawl log entry
        crawl_log = CrawlLog(
            site_name=site_name,
            start_time=start_time,
            status="running"
        )
        await crawl_log.insert()
        log_id = crawl_log.id
        
        saved_count = 0
        skipped_count = 0
        article_ids = []
        
        try:
            crawler = await self.get_crawler(site_name, base_url)
            
            async with crawler:
                results = await crawler.crawl()
            
            for article_data in results:
                # Check if URL already exists
                url_hash = article_data.get('url_hash')
                if url_hash:
                    existing = await CrawlResult.find_one(CrawlResult.url_hash == url_hash)
                    if existing:
                        skipped_count += 1
                        continue
                
                # Create new crawl result
                crawl_result = CrawlResult(
                    source_url=article_data.get('source_url'),
                    title=article_data.get('title'),
                    content=article_data.get('content'),
                    meta=article_data.get('meta', {}),
                    source_site=article_data.get('source_site', site_name),
                    url_hash=url_hash or '',
                )
                
                await crawl_result.insert()
                saved_count += 1
                article_ids.append(str(crawl_result.id))
            
            # Update crawler config last_crawl
            config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
            if config:
                now = datetime.datetime.now(datetime.timezone.utc)
                config.last_crawl = now
                # Note: last_scheduled_crawl is only updated by Celery scheduled tasks, not manual runs
                await config.save()
            
            # Remove from active crawls
            CrawlerService._active_crawls.pop(site_name, None)
            
            # Update crawl log with completion
            end_time = datetime.datetime.now(datetime.timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            # Reload log to update it
            crawl_log = await CrawlLog.get(log_id)
            if crawl_log:
                crawl_log.end_time = end_time
                crawl_log.status = "completed"
                crawl_log.articles_found = len(results)
                crawl_log.articles_saved = saved_count
                crawl_log.articles_skipped = skipped_count
                crawl_log.article_ids = article_ids
                crawl_log.duration_seconds = duration
                await crawl_log.save()
            
            return {
                "site_name": site_name,
                "articles_found": len(results),
                "articles_saved": saved_count,
                "articles_skipped": skipped_count,
                "success": True,
                "log_id": str(log_id)
            }
            
        except Exception as e:
            # Remove from active crawls on error
            CrawlerService._active_crawls.pop(site_name, None)
            
            # Update crawl log with error
            end_time = datetime.datetime.now(datetime.timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            # Reload log to update it
            crawl_log = await CrawlLog.get(log_id)
            if crawl_log:
                crawl_log.end_time = end_time
                crawl_log.status = "failed"
                crawl_log.articles_found = len(results) if 'results' in locals() else 0
                crawl_log.articles_saved = saved_count
                crawl_log.articles_skipped = skipped_count
                crawl_log.article_ids = article_ids
                crawl_log.error_message = str(e)
                crawl_log.duration_seconds = duration
                await crawl_log.save()
            
            return {
                "site_name": site_name,
                "success": False,
                "error": str(e),
                "log_id": str(log_id)
            }
    
    @classmethod
    async def get_active_crawls(cls) -> Dict[str, bool]:
        """Get list of currently active crawls from both in-memory and database"""
        now = datetime.datetime.now(datetime.timezone.utc)
        active = {}
        
        # Check in-memory active crawls (for crawls started from FastAPI)
        for site_name, start_time in cls._active_crawls.items():
            diff_seconds = (now - start_time).total_seconds()
            # Consider active if started within last 5 minutes
            if diff_seconds < 300:
                active[site_name] = True
        
        # Clean up old entries
        cls._active_crawls = {
            k: v for k, v in cls._active_crawls.items()
            if (now - v).total_seconds() < 300
        }
        
        # Also check database for running crawls (from Celery tasks)
        try:
            running_logs = await CrawlLog.find(
                CrawlLog.status == "running"
            ).to_list()
            
            for log in running_logs:
                # Consider active if started within last 5 minutes
                if log.start_time:
                    diff_seconds = (now - log.start_time).total_seconds()
                    if diff_seconds < 300:
                        active[log.site_name] = True
        except Exception:
            pass  # If database query fails, just use in-memory tracking
        
        return active
    
    async def get_crawl_stats(self, site_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about crawled data"""
        if site_name:
            results = await CrawlResult.find(CrawlResult.source_site == site_name).to_list()
        else:
            results = await CrawlResult.find_all().to_list()
        
        total = len(results)
        processed = sum(1 for r in results if r.is_processed)
        
        return {
            "total_articles": total,
            "processed_articles": processed,
            "unprocessed_articles": total - processed,
            "site_name": site_name or "all"
        }
