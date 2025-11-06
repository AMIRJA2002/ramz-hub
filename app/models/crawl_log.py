from beanie import Document
from pydantic import Field
from typing import Optional, List
from datetime import datetime, timezone


class CrawlLog(Document):
    """Log entry for each crawl operation"""
    site_name: str = Field(..., max_length=100)
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    status: str = Field(default="running")  # "running", "completed", "failed"
    articles_found: int = Field(default=0)
    articles_saved: int = Field(default=0)
    articles_skipped: int = Field(default=0)
    article_ids: List[str] = Field(default_factory=list)  # List of article IDs
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    
    class Settings:
        name = "crawl_logs"
        indexes = [
            "site_name",
            "start_time",
            "status",
        ]
    
    def __repr__(self):
        return f"<CrawlLog(site_name={self.site_name}, status={self.status}, articles_saved={self.articles_saved})>"

