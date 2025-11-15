from beanie import Document
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class CrawlerConfig(Document):
    site_name: str = Field(..., max_length=100)
    base_url: str = Field(..., max_length=500)
    is_active: bool = Field(default=True)
    crawl_interval_minutes: int = Field(default=15)
    config: Optional[Dict[str, Any]] = None
    last_crawl: Optional[datetime] = None
    last_scheduled_crawl: Optional[datetime] = None  # Track last scheduled crawl (excludes manual runs)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "crawler_configs"
        indexes = [
            [("site_name", 1)],  # Unique index will be created separately
            "is_active"
        ]
    
    def __repr__(self):
        return f"<CrawlerConfig(id={self.id}, site_name={self.site_name}, is_active={self.is_active})>"
