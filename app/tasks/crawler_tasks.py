"""
Celery tasks for crawler operations
"""
from celery import Task
from app.celery_app import celery_app
from app.services.crawler_service import CrawlerService
from app.database import connect_to_mongo, close_mongo_connection
from app.models.crawler_config import CrawlerConfig
import asyncio
import logging

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """Base task class that handles async operations"""
    
    def __call__(self, *args, **kwargs):
        """Execute async task in event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_async(*args, **kwargs))
        finally:
            loop.close()
    
    async def run_async(self, *args, **kwargs):
        """Override this method in subclasses"""
        raise NotImplementedError


@celery_app.task(
    bind=True,
    base=AsyncTask,
    name='app.tasks.crawler_tasks.crawl_site_task',
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=1800,  # 30 minutes max
    retry_jitter=True,
)
class CrawlSiteTask(AsyncTask):
    """Task to crawl a specific site"""
    
    async def run_async(self, site_name: str, base_url: str = None):
        """
        Crawl a specific site
        
        Args:
            site_name: Name of the site to crawl
            base_url: Base URL for the crawler (optional)
        
        Returns:
            dict: Crawl result with statistics
        """
        try:
            logger.info(f"Starting crawl task for {site_name}")
            
            # Connect to database
            await connect_to_mongo()
            
            # Execute crawl using existing service
            service = CrawlerService()
            result = await service.crawl_site(site_name, base_url)
            
            logger.info(
                f"Completed crawl for {site_name}: "
                f"{result.get('articles_saved', 0)} articles saved, "
                f"{result.get('articles_skipped', 0)} skipped"
            )
            
            return result
            
        except Exception as exc:
            logger.error(f"Error crawling {site_name}: {str(exc)}")
            # Re-raise to trigger retry
            raise
        
        finally:
            # Clean up database connection
            try:
                await close_mongo_connection()
            except:
                pass


# Create task instance
crawl_site_task = CrawlSiteTask()


@celery_app.task(
    bind=True,
    base=AsyncTask,
    name='app.tasks.crawler_tasks.update_schedules_task',
    max_retries=3,
)
class UpdateSchedulesTask(AsyncTask):
    """Task to reload schedules from database"""
    
    async def run_async(self):
        """
        Reload crawler schedules from database
        
        This allows dynamic schedule updates without restarting beat
        """
        try:
            logger.info("Reloading crawler schedules from database")
            
            # Connect to database
            await connect_to_mongo()
            
            # Load schedules
            from app.celery_app import load_beat_schedule
            schedule = await load_beat_schedule()
            
            logger.info(f"Reloaded {len(schedule)} crawler schedules")
            
            return {
                'success': True,
                'schedules_loaded': len(schedule),
                'schedules': list(schedule.keys())
            }
            
        except Exception as exc:
            logger.error(f"Error reloading schedules: {str(exc)}")
            raise
        
        finally:
            try:
                await close_mongo_connection()
            except:
                pass


# Create task instance
update_schedules_task = UpdateSchedulesTask()


@celery_app.task(
    name='app.tasks.crawler_tasks.test_task',
    bind=True
)
def test_task(self):
    """Simple test task to verify Celery is working"""
    logger.info("Test task executed successfully")
    return {
        'status': 'success',
        'message': 'Celery is working correctly',
        'task_id': self.request.id
    }
