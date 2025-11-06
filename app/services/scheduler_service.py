from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.crawler_service import CrawlerService
from app.models.crawler_config import CrawlerConfig
from app.config import settings
import asyncio


class SchedulerService:
    """Service for scheduling periodic crawls"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.crawler_service = CrawlerService()
        self.is_running = False
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            return
        
        if settings.ENABLE_SCHEDULER:
            self.scheduler.start()
            self.is_running = True
            
            # Load all active configs and create individual jobs for each site
            # Each site uses its own crawl_interval_minutes from config
            await self._load_and_schedule_active_sites()
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
        self.is_running = False
    
    async def _load_and_schedule_active_sites(self):
        """Load all active configs and schedule individual jobs for each site"""
        try:
            configs = await CrawlerConfig.find(CrawlerConfig.is_active == True).to_list()
            
            print(f"Loading {len(configs)} active crawler configurations...")
            for config in configs:
                # Create individual job for each site with its own interval
                self.add_site_job(config.site_name, config.crawl_interval_minutes)
                
            print(f"Scheduled {len(configs)} crawler jobs")
        except Exception as e:
            print(f"Error loading active sites for scheduling: {str(e)}")
    
    def add_site_job(self, site_name: str, interval_minutes: int):
        """Add a specific job for a site with its own interval"""
        if not self.is_running or not self.scheduler.running:
            # If scheduler not running yet, job will be added when scheduler starts
            return
        
        async def crawl_job():
            try:
                # Get config to get base_url
                config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
                if config and config.is_active:
                    print(f"Running scheduled crawl for {site_name}...")
                    await self.crawler_service.crawl_site(site_name, config.base_url)
                else:
                    # If site is no longer active, remove the job
                    self.remove_site_job(site_name)
            except Exception as e:
                print(f"Error in scheduled crawl for {site_name}: {str(e)}")
        
        # Add job with site-specific interval
        self.scheduler.add_job(
            crawl_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=f"crawl_{site_name}",
            replace_existing=True
        )
        print(f"✓ Scheduled job for '{site_name}' with interval {interval_minutes} minutes")
    
    def remove_site_job(self, site_name: str):
        """Remove a site's scheduled job"""
        try:
            self.scheduler.remove_job(f"crawl_{site_name}")
        except Exception:
            pass
