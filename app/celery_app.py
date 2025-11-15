from celery import Celery
from celery.signals import worker_process_init, task_prerun
from app.config import settings
import asyncio
import sys
import traceback
from app.services.crawler_service import CrawlerService
from app.models.crawler_config import CrawlerConfig
from app.database import connect_to_mongo
from datetime import datetime, timezone, timedelta

# Create Celery app
print(f"[Celery Init] Creating Celery app...")
print(f"[Celery Init] Broker URL: {settings.CELERY_BROKER_URL}")
print(f"[Celery Init] Result Backend: {settings.CELERY_RESULT_BACKEND}")

celery_app = Celery(
    "rasad_pedia",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.celery_app"]
)

print(f"[Celery Init] Celery app created: {celery_app.main}")

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
    task_always_eager=False,
    task_eager_propagates=True,
)

# Celery Beat schedule - check every minute for sites that need crawling
if settings.ENABLE_SCHEDULER:
    celery_app.conf.beat_schedule = {
        "check-and-crawl-active-sites": {
            "task": "app.celery_app.check_and_crawl_active_sites",
            "schedule": 60.0,  # Run every minute
        },
    }
    print(f"[Celery Init] Beat schedule configured: {list(celery_app.conf.beat_schedule.keys())}")
else:
    print("[Celery Init] WARNING: Scheduler is DISABLED (ENABLE_SCHEDULER=false)")

# Track if database is initialized
_db_initialized = False

def _init_database():
    """Initialize database connection - called on worker startup and before tasks"""
    global _db_initialized
    if _db_initialized:
        return True
    
    try:
        print("=" * 50)
        print("[DB Init] Initializing database connection...")
        print(f"[DB Init] MongoDB URL: {settings.MONGODB_URL}")
        print(f"[DB Init] MongoDB DB: {settings.MONGODB_DB_NAME}")
        
        # Create new event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        print("[DB Init] Connecting to MongoDB...")
        loop.run_until_complete(connect_to_mongo())
        _db_initialized = True
        print("[DB Init] Database connection initialized successfully!")
        print("=" * 50)
        return True
    except Exception as e:
        print(f"[DB Init] ERROR initializing database: {str(e)}")
        traceback.print_exc()
        _db_initialized = False
        print("=" * 50)
        return False

# Initialize database connection for Celery workers
@worker_process_init.connect
def init_worker(**kwargs):
    """Initialize database connection when Celery worker starts"""
    _init_database()

# Ensure database is connected before each task
@task_prerun.connect
def ensure_db_connection(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Ensure database is connected before running task"""
    print(f"[Task PreRun] Task {task.name if task else 'unknown'} (ID: {task_id}) starting")
    if not _init_database():
        raise RuntimeError("Failed to initialize database connection")


# Helper function to run async code in Celery tasks
def run_async(coro):
    """Run async function in Celery task"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        print(f"Error in run_async: {str(e)}")
        traceback.print_exc()
        raise


@celery_app.task(name="app.celery_app.crawl_site_task", bind=True)
def crawl_site_task(self, site_name: str, base_url: str = None, is_scheduled: bool = False):
    """Celery task to crawl a site"""
    print("=" * 60)
    print(f"[Celery Task] ===== STARTING CRAWL TASK =====")
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


@celery_app.task(name="app.celery_app.check_and_crawl_active_sites", bind=True)
def check_and_crawl_active_sites(self):
    """Check all active configs and trigger crawls for sites that need it"""
    print("=" * 60)
    print("[Celery Beat] ===== TASK STARTED: check_and_crawl_active_sites =====")
    print("=" * 60)
    
    async def _check_and_trigger():
        try:
            if not settings.ENABLE_SCHEDULER:
                print("[Celery Beat] Scheduler is disabled")
                return {"message": "Scheduler is disabled"}
            
            from app.models.crawl_log import CrawlLog
            
            print("[Celery Beat] Fetching active configs...")
            configs = await CrawlerConfig.find(CrawlerConfig.is_active == True).to_list()
            print(f"[Celery Beat] Found {len(configs)} active configs")
            
            now = datetime.now(timezone.utc)
            triggered = []
            
            # Get currently running crawls to avoid duplicates
            print("[Celery Beat] Checking for running crawls...")
            running_logs = await CrawlLog.find(
                CrawlLog.status == "running"
            ).to_list()
            running_sites = {log.site_name for log in running_logs}
            print(f"[Celery Beat] Found {len(running_sites)} running crawls")
            
            for config in configs:
                # Skip if already running
                if config.site_name in running_sites:
                    print(f"[Celery Beat] Skipping {config.site_name} - already running")
                    continue
                
                # Check if it's time to crawl (based on scheduled crawls only, not manual)
                should_crawl = False
                
                # Use last_scheduled_crawl if available, otherwise last_crawl as fallback
                last_scheduled = config.last_scheduled_crawl or config.last_crawl
                
                if not last_scheduled:
                    # Never crawled, should crawl now
                    should_crawl = True
                    print(f"[Celery Beat] {config.site_name} - never crawled, triggering now")
                else:
                    # Ensure last_scheduled is timezone-aware
                    if last_scheduled.tzinfo is None:
                        last_scheduled = last_scheduled.replace(tzinfo=timezone.utc)
                    
                    # Check if interval has passed since last scheduled crawl
                    time_since_last = now - last_scheduled
                    interval = timedelta(minutes=config.crawl_interval_minutes)
                    if time_since_last >= interval:
                        should_crawl = True
                        print(f"[Celery Beat] {config.site_name} - interval passed ({time_since_last.total_seconds()/60:.1f} min >= {config.crawl_interval_minutes} min)")
                    else:
                        remaining = interval - time_since_last
                        print(f"[Celery Beat] {config.site_name} - waiting ({remaining.total_seconds()/60:.1f} min remaining)")
                
                if should_crawl:
                    # Trigger crawl task asynchronously (mark as scheduled)
                    print(f"[Celery Beat] Triggering crawl task for {config.site_name}")
                    task_result = crawl_site_task.delay(config.site_name, config.base_url, is_scheduled=True)
                    print(f"[Celery Beat] Task {task_result.id} queued for {config.site_name}")
                    triggered.append(config.site_name)
            
            result = {
                "checked": len(configs),
                "triggered": triggered,
                "count": len(triggered)
            }
            print(f"[Celery Beat] Check complete: {result}")
            return result
        except Exception as e:
            error_msg = f"Error checking active sites: {str(e)}"
            print(f"[Celery Beat] {error_msg}")
            traceback.print_exc()
            return {"error": str(e)}
    
    try:
        result = run_async(_check_and_trigger())
        return result
    except Exception as e:
        error_msg = f"Error in check_and_crawl_active_sites: {str(e)}"
        print(f"[Celery Beat] {error_msg}")
        traceback.print_exc()
        raise

