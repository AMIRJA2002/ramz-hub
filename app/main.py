from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.routers import crawler_router, stats_router
from app.services.scheduler_service import SchedulerService
from app.database import connect_to_mongo, close_mongo_connection


scheduler_service = SchedulerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    await connect_to_mongo()
    await scheduler_service.start()
    
    yield
    
    # Shutdown
    await scheduler_service.stop()
    await close_mongo_connection()


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(crawler_router.router)
app.include_router(stats_router.router)


@app.get("/")
async def root():
    return {
        "message": "Rasad Pedia Crawler API",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
