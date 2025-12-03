# Rasad Pedia Frontend

A modern React dashboard for monitoring and managing the Rasad Pedia crawler system.

## Features

- **Active Crawls Dashboard**: View all active crawler configurations and their status
- **Crawl Results**: Browse and filter crawled articles
- **Statistics Overview**: Real-time statistics about crawling activity
- **Real-time Updates**: Auto-refreshing data for live monitoring

## Development

### Prerequisites

- Node.js 18+ and npm

### Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## Docker

The frontend is containerized and can be run with docker-compose:

```bash
docker-compose up frontend
```

The frontend will be available at `http://localhost:3000`

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: `http://localhost:8003`)


