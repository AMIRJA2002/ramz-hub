from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = "mongodb://mongodb:27017"
    MONGODB_DB_NAME: str = "rasad_pedia"
    
    # Crawler Settings
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_MAX_CONCURRENT: int = 10
    CRAWLER_RETRY_ATTEMPTS: int = 3
    CRAWLER_RETRY_DELAY: int = 5
    
    # Scheduler
    ENABLE_SCHEDULER: bool = True
    CRAWL_INTERVAL_MINUTES: int = 15
    
    # API
    API_TITLE: str = "Rasad Pedia Crawler API"
    API_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
