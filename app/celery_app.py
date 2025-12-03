from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init, task_prerun
from app.config import settings
import asyncio
import traceback
from app.database import connect_to_mongo

# Create Celery app
print(f"[Celery Init] Creating Celery app...")
print(f"[Celery Init] Broker URL: {settings.CELERY_BROKER_URL}")
print(f"[Celery Init] Result Backend: {settings.CELERY_RESULT_BACKEND}")

celery_app = Celery(
    "rasad_pedia",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.celery_app",
        "app.tasks.coindesk_task",
        "app.tasks.crypto_news_task",
        "app.tasks.coinbase_task",
        "app.tasks.general_tasks",
    ]
)

print(f"[Celery Init] Celery app created: {celery_app.main}")

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_always_eager=False,
    task_eager_propagates=True,
    task_create_missing_queues=True,
    task_default_queue='default',
)

# Track if database is initialized
_db_initialized = False

def _init_database():
    """Initialize database connection - called on worker startup and before tasks"""
    global _db_initialized
    if _db_initialized:
        return True
    
    try:
        print("=" * 50)
        print("[DB Init] Initializing database connection...")
        print(f"[DB Init] MongoDB URL: {settings.MONGODB_URL}")
        print(f"[DB Init] MongoDB DB: {settings.MONGODB_DB_NAME}")
        
        # Create new event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        print("[DB Init] Connecting to MongoDB...")
        loop.run_until_complete(connect_to_mongo())
        _db_initialized = True
        print("[DB Init] Database connection initialized successfully!")
        print("=" * 50)
        return True
    except Exception as e:
        print(f"[DB Init] ERROR initializing database: {str(e)}")
        traceback.print_exc()
        _db_initialized = False
        print("=" * 50)
        return False

# Initialize database connection for Celery workers
@worker_process_init.connect
def init_worker(**kwargs):
    """Initialize database connection when Celery worker starts"""
    _init_database()

# Ensure database is connected before each task
@task_prerun.connect
def ensure_db_connection(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Ensure database is connected before running task"""
    print(f"[Task PreRun] Task {task.name if task else 'unknown'} (ID: {task_id}) starting")
    if not _init_database():
        raise RuntimeError("Failed to initialize database connection")


# Import all tasks to register them with Celery (after celery_app is defined)
# This ensures tasks are registered when the module is imported
print("\n[Celery Init] Importing tasks...")
try:
    from app.tasks import coindesk_task, crypto_news_task, coinbase_task, general_tasks
    print("[Celery Init] ✓ All tasks imported successfully")
except Exception as e:
    print(f"[Celery Init] ✗ ERROR importing tasks: {e}")
    import traceback
    traceback.print_exc()

# Print registered tasks for debugging
print(f"\n[Celery Init] Registered tasks ({len([t for t in celery_app.tasks.keys() if not t.startswith('celery.')])} user tasks):")
for task_name in sorted(celery_app.tasks.keys()):
    if not task_name.startswith('celery.'):  # Skip internal celery tasks
        task_obj = celery_app.tasks[task_name]
        print(f"  - {task_name} ({task_obj})")


# ============================================================================
# Celery Beat Schedule Configuration
# ============================================================================

if settings.ENABLE_SCHEDULER:
    celery_app.conf.beat_schedule = {
        "crawl_coindesk_schedule": {
            "task": "app.celery_app.crawl_coindesk",
            "schedule": 60 * 60.0,  # Every 15 minutes
            "options": {"queue": "coindesk"},
        },
        "crawl_crypto_news_schedule": {
            "task": "app.celery_app.crawl_crypto_news",
            "schedule": 60 * 60.0,  # Every 15 minutes
            "options": {"queue": "crypto_news"},
        },
        "crawl_coinbase_schedule": {
            "task": "app.celery_app.crawl_coinbase",
            "schedule": 60 * 60.0,  # Every 30 minutes
            "options": {"queue": "coinbase"},
        },
    }
    
    print(f"\n[Celery Init] Beat schedule configured with {len(celery_app.conf.beat_schedule)} crawlers:")
    for schedule_name, schedule_config in celery_app.conf.beat_schedule.items():
        task_name = schedule_config["task"]
        schedule = schedule_config["schedule"]
        queue = schedule_config.get("options", {}).get("queue", "default")
        
        # Verify task exists
        task_exists = task_name in celery_app.tasks
        status = "✓" if task_exists else "✗ MISSING"
        
        if isinstance(schedule, (int, float)):
            interval_min = schedule / 60
            print(f"  {status} {schedule_name}: {task_name} (every {interval_min:.0f} minutes) -> queue: {queue}")
        else:
            print(f"  {status} {schedule_name}: {task_name} ({schedule}) -> queue: {queue}")
        
        if not task_exists:
            print(f"    WARNING: Task '{task_name}' not found in registered tasks!")
            print(f"    Available tasks: {[t for t in celery_app.tasks.keys() if not t.startswith('celery.')]}")
        else:
            # Additional verification: try to get the task object
            try:
                task_obj = celery_app.tasks[task_name]
                print(f"    Task object: {task_obj} (queue: {queue})")
            except Exception as e:
                print(f"    ERROR accessing task: {e}")
else:
    print("[Celery Init] WARNING: Scheduler is DISABLED (ENABLE_SCHEDULER=false)")



