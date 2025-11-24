# Recent Changes

## Port Changes

### MongoDB External Port
- **Old**: `27017:27017`
- **New**: `27018:27017`
- **Access**: `mongodb://rasad_admin:MongoDB_Strong_Pass_2024@localhost:27018`

Internal containers still use `mongodb:27017`, only external access changed to port `27018`.

## Celery Worker Hostname

### Worker Name
- **Old**: `celery@7272cb9acff5` (random container ID)
- **New**: `crawler_worker@41bbb8fcb550` (descriptive name)

This makes it easier to identify the worker in Flower and logs.

## Verification

✅ MongoDB accessible on port 27018
✅ Worker hostname changed to `crawler_worker@*`
✅ All services still working
✅ Crawlers still running
✅ Data intact (3 crawler configs)

## Updated Files

- `docker-compose.yml`:
  - MongoDB port mapping: `27018:27017`
  - Worker command: Added `--hostname=crawler_worker@%h`
