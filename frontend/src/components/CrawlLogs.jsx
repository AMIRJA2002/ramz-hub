import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle2, XCircle, RefreshCw, FileText, Filter } from 'lucide-react';
import { crawlerAPI } from '../services/api';
import { useDarkMode } from '../contexts/DarkModeContext';
import { formatDateTimeWithTehranTime } from '../utils/timeFormatter';

const CrawlLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [siteFilter, setSiteFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [availableSites, setAvailableSites] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const { isDark } = useDarkMode();
  const itemsPerPage = 20;

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = {
        limit: itemsPerPage,
        offset: currentPage * itemsPerPage,
      };
      if (siteFilter) params.site_name = siteFilter;
      if (statusFilter) params.status = statusFilter;
      
      const data = await crawlerAPI.getLogs(params);
      setLogs(data);
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConfigs = async () => {
    try {
      const configs = await crawlerAPI.getConfigs();
      const sites = [...new Set(configs.map(c => c.site_name))];
      setAvailableSites(sites);
    } catch (error) {
      console.error('Error fetching configs:', error);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [siteFilter, statusFilter, currentPage]);

  const formatDate = (dateString) => {
    return formatDateTimeWithTehranTime(dateString);
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs.toFixed(1)}s`;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return (
          <span className="px-2 py-1 bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 text-xs font-medium rounded">
            Completed
          </span>
        );
      case 'failed':
        return (
          <span className="px-2 py-1 bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 text-xs font-medium rounded">
            Failed
          </span>
        );
      case 'running':
        return (
          <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 text-xs font-medium rounded animate-pulse">
            Running
          </span>
        );
      default:
        return (
          <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="glass-card dark:glass-card-dark rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <FileText className="w-6 h-6 text-white dark:text-primary-300 drop-shadow-lg" />
          <h2 className="text-2xl font-bold text-white dark:text-gray-100 drop-shadow-lg">Crawl Logs</h2>
        </div>
        <button
          onClick={fetchLogs}
          className="flex items-center gap-2 px-4 py-2 glass-button dark:glass-button text-white rounded-lg hover:scale-105 transition-all font-medium"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1">
          <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/70 dark:text-gray-400 z-10" />
          <select
            value={siteFilter}
            onChange={(e) => {
              setSiteFilter(e.target.value);
              setCurrentPage(0);
            }}
            className="pl-10 pr-4 py-2 w-full glass-input dark:glass-input text-white dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-white/30 focus:border-white/50"
          >
            <option value="" className="bg-gray-800 text-white">All Sites</option>
            {availableSites.map((site) => (
              <option key={site} value={site} className="bg-gray-800 text-white">
                {site}
              </option>
            ))}
          </select>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setCurrentPage(0);
          }}
          className="px-4 py-2 glass-input dark:glass-input text-white dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-white/30 focus:border-white/50"
        >
          <option value="" className="bg-gray-800 text-white">All Status</option>
          <option value="completed" className="bg-gray-800 text-white">Completed</option>
          <option value="failed" className="bg-gray-800 text-white">Failed</option>
          <option value="running" className="bg-gray-800 text-white">Running</option>
        </select>
      </div>

      {loading && logs.length === 0 ? (
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 glass-card dark:glass-card-dark rounded-xl"></div>
          ))}
        </div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 text-white/70 dark:text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-4 text-white/30 dark:text-gray-600" />
          <p>No crawl logs found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`glass-card dark:glass-card-dark rounded-xl p-4 hover:shadow-lg transition-all ${
                log.status === 'running'
                  ? 'border-purple-400 dark:border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                  : log.status === 'failed'
                  ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-white dark:text-gray-100 drop-shadow">
                      {log.site_name}
                    </h3>
                    {getStatusBadge(log.status)}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="flex items-center gap-2 text-white/80 dark:text-gray-300">
                      <Clock className="w-4 h-4" />
                      <div>
                        <div className="font-medium">Started</div>
                        <div className="text-xs">{formatDate(log.start_time)}</div>
                      </div>
                    </div>
                    {log.end_time && (
                      <div className="flex items-center gap-2 text-white/80 dark:text-gray-300">
                        <CheckCircle2 className="w-4 h-4" />
                        <div>
                          <div className="font-medium">Finished</div>
                          <div className="text-xs">{formatDate(log.end_time)}</div>
                        </div>
                      </div>
                    )}
                    {log.duration_seconds && (
                      <div className="flex items-center gap-2 text-white/80 dark:text-gray-300">
                        <RefreshCw className="w-4 h-4" />
                        <div>
                          <div className="font-medium">Duration</div>
                          <div className="text-xs">{formatDuration(log.duration_seconds)}</div>
                        </div>
                      </div>
                    )}
                    <div className="text-white/80 dark:text-gray-300">
                      <div className="font-medium">Articles</div>
                      <div className="text-xs">
                        {log.articles_saved} saved / {log.articles_found} found
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {log.status === 'failed' && log.error_message && (
                <div className="mt-3 pt-3 border-t border-red-400/30 dark:border-red-800">
                  <div className="flex items-start gap-2">
                    <XCircle className="w-4 h-4 text-red-300 dark:text-red-400 mt-0.5" />
                    <div className="text-sm text-red-200 dark:text-red-300">
                      <div className="font-medium">Error:</div>
                      <div>{log.error_message}</div>
                    </div>
                  </div>
                </div>
              )}
              
              {log.article_ids && log.article_ids.length > 0 && (
                <div className="mt-3 pt-3 border-t border-white/10 dark:border-gray-700">
                  <div className="text-sm text-white/80 dark:text-gray-300">
                    <div className="font-medium mb-1">
                      Article IDs ({log.article_ids.length}):
                    </div>
                    <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
                      {log.article_ids.slice(0, 10).map((id) => (
                        <span
                          key={id}
                          className="px-2 py-1 bg-white/10 dark:bg-gray-700/50 text-white/80 dark:text-gray-300 text-xs rounded-lg font-mono border border-white/10"
                        >
                          {id.substring(0, 8)}...
                        </span>
                      ))}
                      {log.article_ids.length > 10 && (
                        <span className="px-2 py-1 text-white/60 dark:text-gray-400 text-xs">
                          +{log.article_ids.length - 10} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CrawlLogs;

