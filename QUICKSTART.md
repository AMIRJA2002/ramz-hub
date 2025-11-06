# Quick Start Guide

## Step-by-Step Instructions

### Option 1: Using Docker (Recommended)

#### Step 1: Start the services
```bash
docker-compose up --build
```

Wait for all services to start. You should see:
- ✅ MongoDB running
- ✅ FastAPI app running on port 8000

#### Step 2: Initialize crawler configurations
Open a **new terminal** and run:
```bash
docker-compose exec app python init_crawlers.py
```

You should see output like:
```
Initializing crawler configurations...
✓ Created config for 'coinbase' - https://blog.coinbase.com
✓ Created config for 'coindesk' - https://www.coindesk.com
✓ Created config for 'crypto_news' - https://cryptonews.com

✅ Crawler configurations initialized successfully!

Active crawlers:
  - coinbase: https://blog.coinbase.com (every 15 min)
  - coindesk: https://www.coindesk.com (every 15 min)
```

#### Step 3: Access the application
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:3000

#### Step 4: Test crawling
You can test by triggering a crawl:

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/crawler/crawl" \
  -H "Content-Type: application/json" \
  -d '{"site_name": "coinbase"}'
```

**Or using the API docs:**
1. Go to http://localhost:8000/docs
2. Find `POST /api/crawler/crawl`
3. Click "Try it out"
4. Enter `{"site_name": "coinbase"}`
5. Click "Execute"

#### Step 5: View results
```bash
curl "http://localhost:8000/api/crawler/results?limit=5"
```

Or visit: http://localhost:8000/api/crawler/results?limit=5

---

### Option 2: Running Locally (Without Docker)

#### Prerequisites
- Python 3.11+
- MongoDB installed and running locally

#### Step 1: Install Python dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Step 2: Start MongoDB
Make sure MongoDB is running:
```bash
# On Linux/Mac
sudo systemctl start mongod

# Or check if it's running
mongosh
```

#### Step 3: Update MongoDB URL (if needed)
Edit `app/config.py` and change:
```python
MONGODB_URL: str = "mongodb://localhost:27017"  # For local MongoDB
```

#### Step 4: Initialize crawler configurations
```bash
python init_crawlers.py
```

#### Step 5: Start the FastAPI server
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

---

## Verify Everything Works

### 1. Check API health
```bash
curl http://localhost:8000/health
```
Should return: `{"status":"healthy"}`

### 2. List crawler configurations
```bash
curl http://localhost:8000/api/crawler/config
```
Should return a list of 3 crawler configs.

### 3. Get statistics
```bash
curl http://localhost:8000/api/stats/overview
```

### 4. Trigger a crawl
```bash
curl -X POST "http://localhost:8000/api/crawler/crawl" \
  -H "Content-Type: application/json" \
  -d '{"site_name": "coinbase"}'
```

### 5. View results
```bash
curl "http://localhost:8000/api/crawler/results?limit=5"
```

---

## Troubleshooting

### MongoDB connection error
- Make sure MongoDB is running
- Check the `MONGODB_URL` in `app/config.py`
- For Docker: MongoDB service name should be `mongodb`

### Port already in use
- Change ports in `docker-compose.yml` if 8000 or 27017 are taken
- Or stop the service using those ports

### Import errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Rebuild Docker containers: `docker-compose build --no-cache`

### Crawler not finding articles
- Check if the website structure has changed
- Verify the `base_url` is correct
- Check crawler selectors in the crawler classes

---

## Next Steps

1. **View the UI**: Visit http://localhost:3000
2. **Customize crawlers**: Edit crawler classes in `app/crawlers/`
3. **Add more sites**: Use the API to create new crawler configs
4. **Adjust scheduling**: Update `CRAWL_INTERVAL_MINUTES` in config

---

## Useful Commands

### Docker
```bash
# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build

# Access MongoDB shell
docker-compose exec mongodb mongosh
```

### Local Development
```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run on different port
uvicorn app.main:app --port 8080

# Access MongoDB shell
mongosh
```


