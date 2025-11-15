from celery import Celery
from celery.signals import worker_process_init
from app.config import settings
import asyncio
from app.services.crawler_service import CrawlerService
from app.models.crawler_config import CrawlerConfig
from app.database import connect_to_mongo
from datetime import datetime, timezone, timedelta

# Create Celery app
celery_app = Celery(
    "rasad_pedia",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.celery_app"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Celery Beat schedule - check every minute for sites that need crawling
if settings.ENABLE_SCHEDULER:
    celery_app.conf.beat_schedule = {
        "check-and-crawl-active-sites": {
            "task": "app.celery_app.check_and_crawl_active_sites",
            "schedule": 60.0,  # Run every minute
        },
    }

# Initialize database connection for Celery workers
@worker_process_init.connect
def init_worker(**kwargs):
    """Initialize database connection when Celery worker starts"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_to_mongo())


# Helper function to run async code in Celery tasks
def run_async(coro):
    """Run async function in Celery task"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="app.celery_app.crawl_site_task")
def crawl_site_task(site_name: str, base_url: str = None, is_scheduled: bool = False):
    """Celery task to crawl a site"""
    async def _crawl():
        crawler_service = CrawlerService()
        result = await crawler_service.crawl_site(site_name, base_url)
        
        # Update last_scheduled_crawl if this was a scheduled crawl
        if is_scheduled:
            config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
            if config:
                config.last_scheduled_crawl = datetime.now(timezone.utc)
                await config.save()
        
        return result
    
    return run_async(_crawl())


@celery_app.task(name="app.celery_app.check_and_crawl_active_sites")
def check_and_crawl_active_sites():
    """Check all active configs and trigger crawls for sites that need it"""
    async def _check_and_trigger():
        try:
            if not settings.ENABLE_SCHEDULER:
                return {"message": "Scheduler is disabled"}
            
            from app.models.crawl_log import CrawlLog
            
            configs = await CrawlerConfig.find(CrawlerConfig.is_active == True).to_list()
            now = datetime.now(timezone.utc)
            triggered = []
            
            # Get currently running crawls to avoid duplicates
            running_logs = await CrawlLog.find(
                CrawlLog.status == "running"
            ).to_list()
            running_sites = {log.site_name for log in running_logs}
            
            for config in configs:
                # Skip if already running
                if config.site_name in running_sites:
                    continue
                
                # Check if it's time to crawl (based on scheduled crawls only, not manual)
                should_crawl = False
                
                # Use last_scheduled_crawl if available, otherwise last_crawl as fallback
                last_scheduled = config.last_scheduled_crawl or config.last_crawl
                
                if not last_scheduled:
                    # Never crawled, should crawl now
                    should_crawl = True
                else:
                    # Check if interval has passed since last scheduled crawl
                    time_since_last = now - last_scheduled
                    interval = timedelta(minutes=config.crawl_interval_minutes)
                    if time_since_last >= interval:
                        should_crawl = True
                
                if should_crawl:
                    # Trigger crawl task asynchronously (mark as scheduled)
                    crawl_site_task.delay(config.site_name, config.base_url, is_scheduled=True)
                    triggered.append(config.site_name)
            
            return {
                "checked": len(configs),
                "triggered": triggered,
                "count": len(triggered)
            }
        except Exception as e:
            print(f"Error checking active sites: {str(e)}")
            return {"error": str(e)}
    
    return run_async(_check_and_trigger())

