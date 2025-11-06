from beanie import Document
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class CrawlResult(Document):
    source_url: str = Field(..., max_length=500)
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    source_site: str = Field(..., max_length=100)
    crawl_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_processed: bool = Field(default=False)
    url_hash: str = Field(..., max_length=64)
    
    class Settings:
        name = "crawl_results"
        indexes = [
            "source_url",
            "source_site",
            "url_hash",
            "crawl_timestamp"
        ]
    
    def __repr__(self):
        return f"<CrawlResult(id={self.id}, source_site={self.source_site}, title={self.title[:50] if self.title else None})>"
