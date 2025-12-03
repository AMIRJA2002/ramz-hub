import axios from 'axios';

// In production (Docker), use relative path to go through nginx proxy
// In development, use the full URL
// If VITE_API_URL is set, use it; otherwise use relative path in production
const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // In production (when running in Docker), use relative path (nginx will proxy)
  // In development, use localhost
  return import.meta.env.PROD ? '' : 'http://localhost:8003';
};

const API_BASE_URL = getApiBaseUrl();

// Log API base URL for debugging (only in development)
if (!import.meta.env.PROD) {
  console.log('[API] Base URL:', API_BASE_URL || '(relative path - using nginx proxy)');
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    if (!import.meta.env.PROD) {
      console.log('[API] Request:', config.method?.toUpperCase(), config.url);
    }
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('[API] Response error:', {
      message: error.message,
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);

export const crawlerAPI = {
  // Get all crawler configs
  getConfigs: async () => {
    const response = await api.get('/api/crawler/config');
    return response.data;
  },

  // Get crawl results
  getResults: async (siteName = null, limit = 100, offset = 0) => {
    const params = { limit, offset };
    if (siteName) params.site_name = siteName;
    const response = await api.get('/api/crawler/results', { params });
    return response.data;
  },

  // Get stats overview
  getStats: async () => {
    const response = await api.get('/api/stats/overview');
    return response.data;
  },

  // Get site stats
  getSiteStats: async (siteName) => {
    const response = await api.get(`/api/stats/site/${siteName}`);
    return response.data;
  },

  // Trigger crawl
  triggerCrawl: async (siteName, baseUrl = null) => {
    const response = await api.post('/api/crawler/crawl', {
      site_name: siteName,
      base_url: baseUrl,
    });
    return response.data;
  },

  // Get active crawls
  getActiveCrawls: async () => {
    const response = await api.get('/api/crawler/active');
    return response.data;
  },

  // Get crawl logs
  getLogs: async (params = {}) => {
    const response = await api.get('/api/crawler/logs', { params });
    return response.data;
  },

  // Get specific crawl log
  getLog: async (logId) => {
    const response = await api.get(`/api/crawler/logs/${logId}`);
    return response.data;
  },

  // Get Beat schedule information
  getBeatSchedule: async () => {
    const response = await api.get('/api/crawler/beat-schedule');
    return response.data;
  },

  // Get Celery status
  getCeleryStatus: async () => {
    const response = await api.get('/api/crawler/celery-status');
    return response.data;
  },
};

export default api;


