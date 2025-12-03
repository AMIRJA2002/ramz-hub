"""Celery task for CryptoNews crawler"""
from app.celery_app import celery_app
from app.services.crawler_service import CrawlerService
from app.models.crawler_config import CrawlerConfig
from app.tasks.helpers import run_async
from datetime import datetime, timezone
import traceback


@celery_app.task(name="app.celery_app.crawl_crypto_news", bind=True)
def crawl_crypto_news(self):
    """Celery task to crawl CryptoNews"""
    site_name = "crypto_news"
    print("=" * 60)
    print(f"[Celery Task] ===== STARTING CRAWL TASK: {site_name} =====")
    print(f"[Celery Task] Task ID: {self.request.id}")
    print("=" * 60)
    
    async def _crawl():
        try:
            config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
            base_url = config.base_url if config else None
            
            print(f"[Celery Task] Initializing crawler service for {site_name}")
            crawler_service = CrawlerService()
            print(f"[Celery Task] Starting crawl for {site_name}")
            result = await crawler_service.crawl_site(site_name, base_url)
            print(f"[Celery Task] Crawl completed for {site_name}: success={result.get('success', False)}")
            
            if config:
                config.last_scheduled_crawl = datetime.now(timezone.utc)
                await config.save()
                print(f"[Celery Task] Updated last_scheduled_crawl for {site_name}")
            
            return result
        except Exception as e:
            print(f"[Celery Task] ERROR in crawl for {site_name}: {str(e)}")
            traceback.print_exc()
            raise
    
    try:
        result = run_async(_crawl())
        print("=" * 60)
        print(f"[Celery Task] ===== TASK COMPLETED SUCCESSFULLY: {site_name} =====")
        print("=" * 60)
        return result
    except Exception as e:
        print("=" * 60)
        print(f"[Celery Task] ===== TASK FAILED: {site_name} =====")
        print(f"[Celery Task] Error: {str(e)}")
        print("=" * 60)
        traceback.print_exc()
        raise

