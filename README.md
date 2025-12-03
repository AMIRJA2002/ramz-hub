# Rasad Pedia Crawler

Simple cryptocurrency news crawler with Celery scheduling.

## Quick Start

```bash
# Start all services
docker-compose up -d

# Access API
http://localhost:8003/docs
```

## Services

- **API**: http://localhost:8003
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379

## How It Works

1. Create crawler configs in MongoDB with `crawl_interval_minutes`
2. Celery Beat reads configs and schedules periodic crawls
3. Celery Worker executes crawl tasks
4. Results stored in MongoDB

That's it!
