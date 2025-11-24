# MongoDB Connection Guide

## Connection Details

- **Host**: localhost
- **Port**: 27018 (external)
- **Username**: rasad_admin
- **Password**: MongoDB_Strong_Pass_2024
- **Database**: rasad_pedia
- **Auth Database**: admin

## Connection Strings

### Using mongosh (MongoDB Shell)

```bash
# Connect to admin database
mongosh "mongodb://rasad_admin:MongoDB_Strong_Pass_2024@localhost:27018/admin"

# Connect to rasad_pedia database
mongosh "mongodb://rasad_admin:MongoDB_Strong_Pass_2024@localhost:27018/rasad_pedia?authSource=admin"
```

### Using MongoDB Compass (GUI)

```
mongodb://rasad_admin:MongoDB_Strong_Pass_2024@localhost:27018/?authSource=admin
```

### Using Python (pymongo/motor)

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    "mongodb://rasad_admin:MongoDB_Strong_Pass_2024@localhost:27018/?authSource=admin"
)
db = client.rasad_pedia
```

### Using Connection Parameters

```
Host: localhost
Port: 27018
Username: rasad_admin
Password: MongoDB_Strong_Pass_2024
Authentication Database: admin
Database: rasad_pedia
```

## Test Connection

```bash
# Test ping
mongosh "mongodb://rasad_admin:MongoDB_Strong_Pass_2024@localhost:27018/admin" --eval "db.adminCommand('ping')"

# List databases
mongosh "mongodb://rasad_admin:MongoDB_Strong_Pass_2024@localhost:27018/admin" --eval "db.adminCommand('listDatabases')"

# Count crawler configs
mongosh "mongodb://rasad_admin:MongoDB_Strong_Pass_2024@localhost:27018/rasad_pedia?authSource=admin" --eval "db.crawler_configs.countDocuments()"

# View crawler configs
mongosh "mongodb://rasad_admin:MongoDB_Strong_Pass_2024@localhost:27018/rasad_pedia?authSource=admin" --eval "db.crawler_configs.find().pretty()"
```

## Common Issues

### Issue: Authentication failed
**Solution**: Make sure to include `?authSource=admin` in the connection string

### Issue: Connection refused
**Solution**: Check if MongoDB container is running:
```bash
docker ps | grep mongodb
```

### Issue: Wrong port
**Solution**: External port is 27018, not 27017

## Collections

- `crawler_configs` - Crawler configurations
- `crawl_results` - Crawled articles
- `crawl_logs` - Crawl execution logs

## Verified Working ✅

Connection tested and working on port 27018 with authentication.
