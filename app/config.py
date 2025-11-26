from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    MONGODB_USERNAME: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    
    # RabbitMQ
    RABBITMQ_USER: Optional[str] = None
    RABBITMQ_PASSWORD: Optional[str] = None
    
    # Redis
    REDIS_URL: str
    REDIS_PASSWORD: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Crawler Settings
    CRAWLER_USER_AGENT: str
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
    
    # LLM API Keys
    OPENROUTER_API_KEY: str
    GEMINI_API_KEY: str

    # Security
    SECRET_KEY: str
    API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
