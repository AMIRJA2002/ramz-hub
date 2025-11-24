# Data Persistence Configuration

All important data is now persisted across container restarts.

## Persistent Volumes

### 1. MongoDB Data
- **Volume**: `mongodb_data`
- **Mount**: `/data/db`
- **Contains**: All database data (articles, configs, logs)
- **Persists**: ✅ Yes

### 2. RabbitMQ Data
- **Volume**: `rabbitmq_data`
- **Mount**: `/var/lib/rabbitmq`
- **Contains**: Message queue data, exchanges, queues
- **Persists**: ✅ Yes

### 3. Flower Data (NEW)
- **Volume**: `flower_data`
- **Mount**: `/data`
- **File**: `/data/flower.db`
- **Contains**: Task history, worker stats, monitoring data
- **Persists**: ✅ Yes

### 4. Celery Beat Schedule (NEW)
- **Volume**: `celery_beat_data`
- **Mount**: `/data`
- **File**: `/data/celerybeat-schedule`
- **Contains**: Beat scheduler state, last run times
- **Persists**: ✅ Yes

## What This Means

### Before Fix:
- ❌ Flower data lost on restart
- ❌ Beat schedule reset on restart
- ✅ MongoDB data persisted
- ✅ RabbitMQ data persisted

### After Fix:
- ✅ Flower data persists (task history, stats)
- ✅ Beat schedule persists (no duplicate runs)
- ✅ MongoDB data persists
- ✅ RabbitMQ data persists

## Testing Persistence

```bash
# Restart containers
docker compose restart flower celery_beat

# Check Flower data still exists
docker exec rasad_pedia_flower ls -lh /data/flower.db

# Check Beat schedule still exists
docker exec rasad_pedia_celery_beat ls -lh /data/celerybeat-schedule
```

## Volume Management

### List all volumes
```bash
docker volume ls | grep rasad
```

### Inspect a volume
```bash
docker volume inspect rasad-pedia_flower_data
```

### Backup a volume
```bash
docker run --rm -v rasad-pedia_flower_data:/data -v $(pwd):/backup alpine tar czf /backup/flower_backup.tar.gz -C /data .
```

### Remove all volumes (CAUTION: Deletes all data!)
```bash
docker compose down -v
```

## Notes

- Volumes persist even when containers are removed
- Use `docker compose down -v` to remove volumes (deletes all data)
- Use `docker compose down` to keep volumes (preserves data)
- Volumes are stored in Docker's volume directory (usually `/var/lib/docker/volumes/`)

## Verified Working ✅

- Flower data persists across restarts
- Beat schedule persists across restarts
- No data loss on container restart
- All monitoring history preserved
