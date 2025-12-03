import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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


