from fastapi import APIRouter, Query
from typing import Optional
from app.services.crawler_service import CrawlerService
from app.models.crawl_result import CrawlResult
from app.models.crawler_config import CrawlerConfig


router = APIRouter(prefix="/api/stats", tags=["stats"])

crawler_service = CrawlerService()


@router.get("/overview")
async def get_stats_overview():
    """Get overall crawling statistics"""
    # Total articles
    total_articles = await CrawlResult.count()
    
    # Articles by site
    pipeline = [
        {"$group": {"_id": "$source_site", "count": {"$sum": 1}}}
    ]
    articles_by_site = {}
    async for doc in CrawlResult.aggregate(pipeline):
        articles_by_site[doc["_id"]] = doc["count"]
    
    # Active crawlers
    active_crawlers = await CrawlerConfig.find(CrawlerConfig.is_active == True).count()
    
    # Total crawlers
    total_crawlers = await CrawlerConfig.count()
    
    return {
        "total_articles": total_articles,
        "articles_by_site": articles_by_site,
        "active_crawlers": active_crawlers,
        "total_crawlers": total_crawlers,
    }


@router.get("/site/{site_name}")
async def get_site_stats(site_name: str):
    """Get statistics for a specific site"""
    stats = await crawler_service.get_crawl_stats(site_name)
    return stats
