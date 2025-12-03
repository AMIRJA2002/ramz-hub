from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.services.crawler_service import CrawlerService
from app.models.crawler_config import CrawlerConfig
from app.models.crawl_result import CrawlResult
from app.models.crawl_log import CrawlLog
from app.celery_app import celery_app
from app.tasks.general_tasks import crawl_site_task, test_task
from celery.schedules import crontab


router = APIRouter(prefix="/api/crawler", tags=["crawler"])

crawler_service = CrawlerService()


class CrawlerConfigCreate(BaseModel):
    site_name: str
    base_url: str
    is_active: bool = True
    crawl_interval_minutes: int = 15
    config: Optional[dict] = None


class CrawlerConfigUpdate(BaseModel):
    is_active: Optional[bool] = None
    crawl_interval_minutes: Optional[int] = None
    config: Optional[dict] = None


class CrawlRequest(BaseModel):
    site_name: str
    base_url: Optional[str] = None


@router.post("/config", response_model=dict)
async def create_crawler_config(config: CrawlerConfigCreate):
    """Create a new crawler configuration"""
    # Check if site already exists
    existing = await CrawlerConfig.find_one(CrawlerConfig.site_name == config.site_name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Site {config.site_name} already exists")
    
    crawler_config = CrawlerConfig(
        site_name=config.site_name,
        base_url=config.base_url,
        is_active=config.is_active,
        crawl_interval_minutes=config.crawl_interval_minutes,
        config=config.config
    )
    
    await crawler_config.insert()
    
    # Note: Celery Beat will automatically pick up new active configs
    # No need to manually schedule - the periodic task checks all active configs
    
    return {
        "id": str(crawler_config.id),
        "site_name": crawler_config.site_name,
        "base_url": crawler_config.base_url,
        "is_active": crawler_config.is_active,
        "crawl_interval_minutes": crawler_config.crawl_interval_minutes
    }


def get_next_scheduled_time_from_beat(site_name: str, last_scheduled_crawl: Optional[datetime] = None) -> Optional[datetime]:
    """Get next scheduled crawl time from Beat Schedule"""
    beat_schedule = celery_app.conf.beat_schedule or {}
    now = datetime.now(timezone.utc)
    
    # Find the schedule for this site
    schedule_key = None
    for key, schedule_config in beat_schedule.items():
        if site_name in key.lower() or schedule_config.get("task", "").endswith(f"crawl_{site_name}"):
            schedule_key = key
            break
    
    if not schedule_key:
        return None
    
    schedule_config = beat_schedule[schedule_key]
    schedule_obj = schedule_config.get("schedule")
    
    # Handle different schedule types
    if isinstance(schedule_obj, (int, float)):
        # Interval-based schedule (in seconds)
        interval_seconds = float(schedule_obj)
        # Use last_scheduled_crawl if available
        if last_scheduled_crawl:
            if last_scheduled_crawl.tzinfo is None:
                last_scheduled_crawl = last_scheduled_crawl.replace(tzinfo=timezone.utc)
            next_time = last_scheduled_crawl + timedelta(seconds=interval_seconds)
            # If next time is in the past, calculate from now
            if next_time < now:
                # Find next occurrence from now
                next_time = now + timedelta(seconds=interval_seconds)
        else:
            # Never crawled, next crawl is at next interval
            next_time = now + timedelta(seconds=interval_seconds)
        return next_time
    elif isinstance(schedule_obj, crontab):
        # Crontab-based schedule
        # Get next run time from crontab
        next_time = schedule_obj.remaining_estimate(datetime.now(timezone.utc))
        if next_time:
            return next_time
        return None
    else:
        return None


@router.get("/config", response_model=List[dict])
async def list_crawler_configs():
    """List all crawler configurations with next scheduled crawl time from Beat Schedule"""
    configs = await CrawlerConfig.find_all().to_list()
    now = datetime.now(timezone.utc)
    
    result = []
    for c in configs:
        config_dict = {
            "id": str(c.id),
            "site_name": c.site_name,
            "base_url": c.base_url,
            "is_active": c.is_active,
            "crawl_interval_minutes": c.crawl_interval_minutes,
            "last_crawl": c.last_crawl.isoformat() if c.last_crawl else None,
            "last_scheduled_crawl": c.last_scheduled_crawl.isoformat() if c.last_scheduled_crawl else None,
            "created_at": c.created_at.isoformat(),
        }
        
        # Calculate next scheduled crawl time from Beat Schedule
        if c.is_active:
            next_crawl = get_next_scheduled_time_from_beat(c.site_name, c.last_scheduled_crawl)
            if next_crawl:
                config_dict["next_scheduled_crawl"] = next_crawl.isoformat()
            else:
                # Fallback to old method if Beat Schedule not found
                last_scheduled = c.last_scheduled_crawl or c.last_crawl
                if last_scheduled:
                    if last_scheduled.tzinfo is None:
                        last_scheduled = last_scheduled.replace(tzinfo=timezone.utc)
                    next_crawl = last_scheduled + timedelta(minutes=c.crawl_interval_minutes)
                    if next_crawl < now:
                        next_crawl = now + timedelta(minutes=c.crawl_interval_minutes)
                else:
                    next_crawl = now + timedelta(minutes=1)
                config_dict["next_scheduled_crawl"] = next_crawl.isoformat()
        else:
            config_dict["next_scheduled_crawl"] = None
        
        result.append(config_dict)
    
    return result


@router.get("/config/{site_name}", response_model=dict)
async def get_crawler_config(site_name: str):
    """Get crawler configuration for a specific site"""
    config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Site {site_name} not found")
    
    now = datetime.now(timezone.utc)
    result = {
        "id": str(config.id),
        "site_name": config.site_name,
        "base_url": config.base_url,
        "is_active": config.is_active,
        "crawl_interval_minutes": config.crawl_interval_minutes,
        "config": config.config,
        "last_crawl": config.last_crawl.isoformat() if config.last_crawl else None,
    }
    
    # Calculate next scheduled crawl time (only for active configs, based on scheduled crawls only)
    if config.is_active:
        # Use last_scheduled_crawl if available, otherwise use last_crawl as fallback
        last_scheduled = config.last_scheduled_crawl or config.last_crawl
        
        if last_scheduled:
            # Ensure timezone-aware datetime
            if last_scheduled.tzinfo is None:
                last_scheduled = last_scheduled.replace(tzinfo=timezone.utc)
            
            next_crawl = last_scheduled + timedelta(minutes=config.crawl_interval_minutes)
            if next_crawl < now:
                next_crawl = now + timedelta(minutes=config.crawl_interval_minutes)
        else:
            next_crawl = now + timedelta(minutes=1)
        result["next_scheduled_crawl"] = next_crawl.isoformat()
    else:
        result["next_scheduled_crawl"] = None
    
    return result


@router.put("/config/{site_name}", response_model=dict)
async def update_crawler_config(
    site_name: str,
    config_update: CrawlerConfigUpdate
):
    """Update crawler configuration"""
    config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Site {site_name} not found")
    
    # Note: Celery Beat will automatically pick up config changes
    # No need to manually update schedules - the periodic task checks all active configs
    
    if config_update.is_active is not None:
        config.is_active = config_update.is_active
    
    if config_update.crawl_interval_minutes is not None:
        config.crawl_interval_minutes = config_update.crawl_interval_minutes
    
    if config_update.config is not None:
        config.config = config_update.config
    
    config.updated_at = datetime.now(timezone.utc)
    await config.save()
    
    return {
        "id": str(config.id),
        "site_name": config.site_name,
        "is_active": config.is_active,
        "crawl_interval_minutes": config.crawl_interval_minutes,
    }


@router.delete("/config/{site_name}")
async def delete_crawler_config(site_name: str):
    """Delete crawler configuration"""
    config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Site {site_name} not found")
    
    # Note: Celery Beat will automatically stop crawling when config is deleted
    # No need to manually remove schedules
    
    await config.delete()
    
    return {"message": f"Configuration for {site_name} deleted"}


@router.post("/crawl", response_model=dict)
async def crawl_site(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Trigger a crawl for a specific site (runs synchronously)"""
    try:
        result = await crawler_service.crawl_site(request.site_name, request.base_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl/background", response_model=dict)
async def crawl_site_background(
    request: CrawlRequest,
    background_tasks: BackgroundTasks
):
    """Trigger a background crawl for a specific site using Celery"""
    try:
        # Trigger Celery task
        task = crawl_site_task.delay(request.site_name, request.base_url)
        return {
            "message": f"Crawl started for {request.site_name} in background",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=dict)
async def get_active_crawls():
    """Get list of currently active/running crawls"""
    active_crawls = await CrawlerService.get_active_crawls()
    return {"active_crawls": active_crawls}


@router.get("/results", response_model=List[dict])
async def get_crawl_results(
    site_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    full_content: bool = False
):
    """Get crawl results
    
    Args:
        site_name: Filter by site name
        limit: Number of results to return
        offset: Number of results to skip
        full_content: If True, return full content. If False, truncate to 500 chars for display
    """
    if site_name:
        query = CrawlResult.find(CrawlResult.source_site == site_name).sort(-CrawlResult.crawl_timestamp)
    else:
        query = CrawlResult.find_all().sort(-CrawlResult.crawl_timestamp)
    
    results = await query.skip(offset).limit(limit).to_list()
    
    return [
        {
            "id": str(r.id),
            "source_url": r.source_url,
            "title": r.title,
            "content": r.content if full_content else (r.content[:500] + "..." if r.content and len(r.content) > 500 else r.content),
            "content_length": len(r.content) if r.content else 0,
            "source_site": r.source_site,
            "crawl_timestamp": r.crawl_timestamp.isoformat(),
            "is_processed": r.is_processed,
            "meta": r.meta,
        }
        for r in results
    ]

@router.get("/article", response_model=None)
async def get_article_by_id(id: str):
    """Get a single crawled article by its ID"""
    try:
        obj_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    article = await CrawlResult.get(obj_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "id": str(article.id),
        "source_url": article.source_url,
        "title": article.title,
        "content": article.content,
        "meta": article.meta,
        "source_site": article.source_site,
        "crawl_timestamp": article.crawl_timestamp.isoformat() if article.crawl_timestamp else None,
        "is_processed": article.is_processed,
        "url_hash": article.url_hash,
    }


@router.get("/logs", response_model=List[dict])
async def get_crawl_logs(
    site_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    """Get crawl logs
    
    Args:
        site_name: Filter by site name
        limit: Number of logs to return
        offset: Number of logs to skip
        status: Filter by status (running, completed, failed)
    """
    query = {}
    if site_name:
        query["site_name"] = site_name
    if status:
        query["status"] = status
    
    if query:
        logs = CrawlLog.find(query).sort(-CrawlLog.start_time)
    else:
        logs = CrawlLog.find_all().sort(-CrawlLog.start_time)
    
    results = await logs.skip(offset).limit(limit).to_list()
    
    return [
        {
            "id": str(log.id),
            "site_name": log.site_name,
            "start_time": log.start_time.isoformat(),
            "end_time": log.end_time.isoformat() if log.end_time else None,
            "status": log.status,
            "articles_found": log.articles_found,
            "articles_saved": log.articles_saved,
            "articles_skipped": log.articles_skipped,
            "article_ids": log.article_ids,
            "error_message": log.error_message,
            "duration_seconds": log.duration_seconds,
        }
        for log in results
    ]


@router.get("/logs/{log_id}", response_model=dict)
async def get_crawl_log(log_id: str):
    """Get a specific crawl log by ID"""
    try:
        obj_id = ObjectId(log_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    log = await CrawlLog.get(obj_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="Crawl log not found")
    
    return {
        "id": str(log.id),
        "site_name": log.site_name,
        "start_time": log.start_time.isoformat(),
        "end_time": log.end_time.isoformat() if log.end_time else None,
        "status": log.status,
        "articles_found": log.articles_found,
        "articles_saved": log.articles_saved,
        "articles_skipped": log.articles_skipped,
        "article_ids": log.article_ids,
        "error_message": log.error_message,
        "duration_seconds": log.duration_seconds,
    }


@router.post("/test-celery", response_model=dict)
async def test_celery_task():
    """Test Celery task execution"""
    try:
        task = test_task.delay()
        return {
            "message": "Test task queued",
            "task_id": task.id,
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error queuing task: {str(e)}")


@router.post("/test-crawler-task/{site_name}", response_model=dict)
async def test_crawler_task(site_name: str):
    """Test a specific crawler task manually"""
    try:
        # Map site names to task functions
        task_map = {
            "coindesk": "app.celery_app.crawl_coindesk",
            "crypto_news": "app.celery_app.crawl_crypto_news",
            "coinbase": "app.celery_app.crawl_coinbase",
        }
        
        if site_name not in task_map:
            raise HTTPException(status_code=400, detail=f"Unknown site: {site_name}. Available: {list(task_map.keys())}")
        
        task_name = task_map[site_name]
        
        # Get the task from celery app
        if task_name not in celery_app.tasks:
            raise HTTPException(status_code=500, detail=f"Task '{task_name}' not found in registered tasks")
        
        task = celery_app.tasks[task_name]
        
        # Execute the task
        result = task.delay()
        
        return {
            "message": f"Crawler task for {site_name} queued",
            "task_id": result.id,
            "task_name": task_name,
            "status": "pending"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error queuing task: {str(e)}")


@router.post("/test-translation-task", response_model=dict)
async def test_translation_task():
    """Test translation task manually"""
    try:
        from app.tasks.translation_task import translate_unprocessed_articles
        
        # Execute the task
        result = translate_unprocessed_articles.delay()
        
        return {
            "message": "Translation task queued",
            "task_id": result.id,
            "task_name": "app.celery_app.translate_unprocessed_articles",
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error queuing translation task: {str(e)}")


@router.get("/beat-schedule", response_model=Dict[str, Any])
async def get_beat_schedule():
    """Get Celery Beat schedule information with next run times"""
    try:
        beat_schedule = celery_app.conf.beat_schedule or {}
        now = datetime.now(timezone.utc)
        
        schedule_info = {}
        for schedule_name, schedule_config in beat_schedule.items():
            task_name = schedule_config.get("task", "")
            schedule_obj = schedule_config.get("schedule")
            queue = schedule_config.get("options", {}).get("queue", "default")
            
            # Calculate next run time
            next_run = None
            if isinstance(schedule_obj, (int, float)):
                # Interval-based schedule
                interval_seconds = float(schedule_obj)
                # Extract site name from schedule name (e.g., "crawl_coindesk_schedule" -> "coindesk")
                site_name = schedule_name.replace("crawl_", "").replace("_schedule", "")
                # Also try to extract from task name
                if not site_name or site_name == schedule_name:
                    task_name_parts = task_name.split(".")
                    if len(task_name_parts) > 0:
                        last_part = task_name_parts[-1]
                        if last_part.startswith("crawl_"):
                            site_name = last_part.replace("crawl_", "")
                
                config = await CrawlerConfig.find_one(CrawlerConfig.site_name == site_name)
                if config and config.last_scheduled_crawl:
                    last_scheduled = config.last_scheduled_crawl
                    if last_scheduled.tzinfo is None:
                        last_scheduled = last_scheduled.replace(tzinfo=timezone.utc)
                    next_run = last_scheduled + timedelta(seconds=interval_seconds)
                    if next_run < now:
                        next_run = now + timedelta(seconds=interval_seconds)
                else:
                    next_run = now + timedelta(seconds=interval_seconds)
            elif isinstance(schedule_obj, crontab):
                # Crontab-based schedule
                next_run = schedule_obj.remaining_estimate(now)
            
            schedule_info[schedule_name] = {
                "task": task_name,
                "schedule": str(schedule_obj),
                "queue": queue,
                "next_run": next_run.isoformat() if next_run else None,
                "next_run_relative": None
            }
            
            # Calculate relative time
            if next_run:
                diff_seconds = (next_run - now).total_seconds()
                if diff_seconds < 60:
                    schedule_info[schedule_name]["next_run_relative"] = f"in {int(diff_seconds)} seconds"
                elif diff_seconds < 3600:
                    schedule_info[schedule_name]["next_run_relative"] = f"in {int(diff_seconds / 60)} minutes"
                elif diff_seconds < 86400:
                    schedule_info[schedule_name]["next_run_relative"] = f"in {int(diff_seconds / 3600)} hours"
                else:
                    schedule_info[schedule_name]["next_run_relative"] = f"in {int(diff_seconds / 86400)} days"
        
        return {
            "schedules": schedule_info,
            "total": len(schedule_info)
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Could not get Beat schedule"
        }


@router.get("/celery-status", response_model=dict)
async def get_celery_status():
    """Get Celery worker and queue status"""
    try:
        inspect = celery_app.control.inspect()
        
        # Get active workers
        active_workers = inspect.active() or {}
        registered_workers = inspect.registered() or {}
        stats = inspect.stats() or {}
        
        # Get scheduled tasks from Beat
        scheduled = inspect.scheduled() or {}
        
        # Get all registered tasks from celery_app
        all_registered_tasks = list(celery_app.tasks.keys())
        user_tasks = [t for t in all_registered_tasks if not t.startswith('celery.')]
        
        return {
            "active_workers": len(active_workers),
            "workers": list(active_workers.keys()),
            "registered_tasks": {
                worker: len(tasks) for worker, tasks in registered_workers.items()
            },
            "all_registered_tasks": user_tasks,
            "scheduled_tasks": scheduled,
            "worker_stats": stats
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Could not inspect Celery workers"
        }
