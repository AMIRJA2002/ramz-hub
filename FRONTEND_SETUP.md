# Frontend Setup - How to View React App

## Prerequisites

1. **Backend must be running** on `http://localhost:8000`
2. **Node.js and npm** installed on your system

## Option 1: Run Frontend Locally (Recommended for Development)

### Step 1: Install Dependencies
```bash
cd frontend
npm install
```

### Step 2: Start Development Server
```bash
npm run dev
```

The frontend will be available at: **http://localhost:5173** (or the port Vite assigns)

### Step 3: Access the App
Open your browser and go to:
- **http://localhost:5173**

## Option 2: Build and Preview (Production-like)

### Step 1: Build the Frontend
```bash
cd frontend
npm install
npm run build
```

### Step 2: Preview the Build
```bash
npm run preview
```

The app will be available at: **http://localhost:4173**

## Option 3: Using Docker (If Docker is Available)

### Start All Services
```bash
docker-compose up -d
```

The frontend will be available at: **http://localhost:3000**

## What You'll See

The React app includes:

1. **Active Crawls Dashboard**
   - Shows all active crawler configurations
   - Displays crawl status, intervals, and last crawl time
   - Real-time updates

2. **Crawl Results**
   - Lists all crawled articles
   - Shows title, content preview, source site, and crawl timestamp
   - Filterable by site name
   - Pagination support

3. **Statistics**
   - Total articles count
   - Articles by site
   - Active vs total crawlers

## Troubleshooting

### Backend Not Running
If you see connection errors, make sure the backend is running:
```bash
# Check if backend is running
curl http://localhost:8000/api/stats/overview

# If not running, start it:
cd /home/amir/Desktop/projects/company/rasad-pedia
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### CORS Issues
If you see CORS errors, make sure:
- Backend is running on `http://localhost:8000`
- Frontend API URL is set correctly in `frontend/src/services/api.js`

### Port Already in Use
If port 5173 is in use, Vite will automatically use the next available port. Check the terminal output for the actual port.

## Quick Start Command

```bash
# Terminal 1: Start Backend (if not running)
cd /home/amir/Desktop/projects/company/rasad-pedia
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Frontend
cd /home/amir/Desktop/projects/company/rasad-pedia/frontend
npm install  # Only needed first time
npm run dev
```

Then open **http://localhost:5173** in your browser!

