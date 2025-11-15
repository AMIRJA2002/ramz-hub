from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.services.crawler_service import CrawlerService
from app.models.crawler_config import CrawlerConfig
from app.models.crawl_result import CrawlResult
from app.models.crawl_log import CrawlLog
from app.celery_app import crawl_site_task


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


@router.get("/config", response_model=List[dict])
async def list_crawler_configs():
    """List all crawler configurations"""
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
            "created_at": c.created_at.isoformat(),
        }
        
        # Calculate next scheduled crawl time (only for active configs, based on scheduled crawls only)
        if c.is_active:
            # Use last_scheduled_crawl if available, otherwise use last_crawl as fallback
            last_scheduled = c.last_scheduled_crawl or c.last_crawl
            
            if last_scheduled:
                # Ensure timezone-aware datetime
                if last_scheduled.tzinfo is None:
                    last_scheduled = last_scheduled.replace(tzinfo=timezone.utc)
                
                # Next crawl = last_scheduled + interval
                next_crawl = last_scheduled + timedelta(minutes=c.crawl_interval_minutes)
                # If next crawl is in the past (should have already run), set to now + interval
                if next_crawl < now:
                    next_crawl = now + timedelta(minutes=c.crawl_interval_minutes)
            else:
                # Never crawled, next crawl is soon (within next minute check cycle)
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
