from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone


class Translation(Document):
    """Translation model for storing translated articles"""
    
    article_id: str = Field(..., description="Reference to the original CrawlResult ID")
    original_title: str = Field(..., max_length=500)
    translated_title: str = Field(..., max_length=500)
    translated_summary: str = Field(...)
    source_site: str = Field(..., max_length=100)
    translation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "translations"
        indexes = [
            "article_id",
            "source_site",
            "translation_timestamp"
        ]
    
    def __repr__(self):
        return f"<Translation(id={self.id}, article_id={self.article_id}, title={self.translated_title[:50]})>"
