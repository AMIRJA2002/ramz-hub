"""General Celery tasks for manual/API calls"""
from app.celery_app import celery_app
from app.services.crawler_service import CrawlerService
from app.models.crawler_config import CrawlerConfig
from app.tasks.helpers import run_async
from datetime import datetime, timezone
import traceback


@celery_app.task(name="app.celery_app.crawl_site_task", bind=True)
def crawl_site_task(self, site_name: str, base_url: str = None, is_scheduled: bool = False):
    """Generic Celery task to crawl a site (used for manual/API calls)"""
    print("=" * 60)
    print(f"[Celery Task] ===== STARTING CRAWL TASK (MANUAL) =====")
    print(f"[Celery Task] Site: {site_name}")
    print(f"[Celery Task] Base URL: {base_url}")
    print(f"[Celery Task] Scheduled: {is_scheduled}")
    print(f"[Celery Task] Task ID: {self.request.id}")
    print("=" * 60)
    
    async def _crawl():
        try:
            print(f"[Celery Task] Initializing crawler service for {site_name}")
            crawler_service = CrawlerService()
            print(f"[Celery Task] Starting crawl for {site_name}")
            result = await crawler_service.crawl_site(site_name, base_url)
            print(f"[Celery Task] Crawl completed for {site_name}: success={result.get('success', False)}")
            
            # Update last_scheduled_crawl if this was a scheduled crawl
            if is_scheduled:
                print(f"[Celery Task] Updating last_scheduled_crawl for {site_name}")
                config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
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
        print(f"[Celery Task] ===== TASK COMPLETED SUCCESSFULLY =====")
        print(f"[Celery Task] Site: {site_name}")
        print("=" * 60)
        return result
    except Exception as e:
        print("=" * 60)
        print(f"[Celery Task] ===== TASK FAILED =====")
        print(f"[Celery Task] Site: {site_name}")
        print(f"[Celery Task] Error: {str(e)}")
        print("=" * 60)
        traceback.print_exc()
        raise


@celery_app.task(name="app.celery_app.test_task")
def test_task():
    """Simple test task to verify Celery is working"""
    print("=" * 60)
    print("[Celery] Test task executed successfully!")
    print("=" * 60)
    return {"status": "success", "message": "Celery is working"}

