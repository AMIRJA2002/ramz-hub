import React, { useState, useEffect } from 'react';
import { Activity, Clock, CheckCircle2, XCircle, RefreshCw, Calendar } from 'lucide-react';
import { crawlerAPI } from '../services/api';
import { useDarkMode } from '../contexts/DarkModeContext';
import { formatDateTimeWithTehranTime, getRelativeTimeUntil } from '../utils/timeFormatter';

const ActiveCrawls = () => {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [crawlingStatus, setCrawlingStatus] = useState({});
  const [activeCrawls, setActiveCrawls] = useState({});
  const { isDark } = useDarkMode();

  const fetchConfigs = async () => {
    try {
      const data = await crawlerAPI.getConfigs();
      setConfigs(data);
    } catch (error) {
      console.error('Error fetching configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchActiveCrawls = async () => {
    try {
      const data = await crawlerAPI.getActiveCrawls();
      setActiveCrawls(data.active_crawls || {});
    } catch (error) {
      console.error('Error fetching active crawls:', error);
    }
  };

  const triggerCrawl = async (siteName, baseUrl) => {
    try {
      setCrawlingStatus(prev => ({ ...prev, [siteName]: 'crawling' }));
      await crawlerAPI.triggerCrawl(siteName, baseUrl);
      setTimeout(() => {
        setCrawlingStatus(prev => ({ ...prev, [siteName]: 'completed' }));
        setTimeout(() => {
          setCrawlingStatus(prev => {
            const newStatus = { ...prev };
            delete newStatus[siteName];
            return newStatus;
          });
        }, 2000);
      }, 1000);
    } catch (error) {
      console.error('Error triggering crawl:', error);
      setCrawlingStatus(prev => ({ ...prev, [siteName]: 'error' }));
    }
  };

  useEffect(() => {
    fetchConfigs();
    fetchActiveCrawls();
    
    // Refresh configs every 5 seconds
    const configInterval = setInterval(fetchConfigs, 5000);
    
    // Refresh active crawls more frequently (every 2 seconds) for real-time updates
    const activeInterval = setInterval(fetchActiveCrawls, 2000);
    
    return () => {
      clearInterval(configInterval);
      clearInterval(activeInterval);
    };
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const activeConfigs = configs.filter(c => c.is_active);
  const inactiveConfigs = configs.filter(c => !c.is_active);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Activity className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Active Crawls</h2>
        </div>
        <button
          onClick={fetchConfigs}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 dark:bg-primary-500 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {activeConfigs.length === 0 && inactiveConfigs.length === 0 ? (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <Activity className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
          <p>No crawler configurations found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {activeConfigs.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3 uppercase tracking-wide">
                Active Sites ({activeConfigs.length})
              </h3>
              <div className="grid gap-4">
                {activeConfigs.map((config) => {
                  const status = crawlingStatus[config.site_name];
                  const isCrawling = status === 'crawling';
                  // Check if crawl is active from backend (scheduled or background crawls)
                  const isBackendCrawling = activeCrawls[config.site_name] === true;
                  const isActiveCrawling = isCrawling || isBackendCrawling;
                  const isCompleted = status === 'completed';
                  const hasError = status === 'error';

                  return (
                    <div
                      key={config.id}
                      className={`border-2 rounded-lg p-4 hover:shadow-md transition-all ${
                        isActiveCrawling
                          ? 'border-purple-400 dark:border-purple-500 bg-purple-50 dark:bg-purple-900/20 animate-blink-purple'
                          : 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            {isActiveCrawling ? (
                              <div className="w-3 h-3 bg-purple-500 dark:bg-purple-400 rounded-full animate-blink-purple shadow-lg shadow-purple-500/50"></div>
                            ) : (
                              <div className="w-3 h-3 bg-green-500 dark:bg-green-400 rounded-full animate-pulse"></div>
                            )}
                            <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                              {config.site_name}
                            </h4>
                            {isActiveCrawling ? (
                              <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 text-xs font-medium rounded animate-pulse">
                                Crawling...
                              </span>
                            ) : (
                              <span className="px-2 py-1 bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 text-xs font-medium rounded">
                                Active
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 truncate">
                            {config.base_url}
                          </p>
                          <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 flex-wrap">
                            <div className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              <span>Every {config.crawl_interval_minutes} min</span>
                            </div>
                            {config.last_crawl && (
                              <div className="flex items-center gap-1">
                                <CheckCircle2 className="w-4 h-4" />
                                <span>
                                  Last: {formatDateTimeWithTehranTime(config.last_crawl)}
                                </span>
                              </div>
                            )}
                            {config.next_scheduled_crawl && !isActiveCrawling && (
                              <div className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
                                <Calendar className="w-4 h-4" />
                                <span>
                                  Next: {getRelativeTimeUntil(config.next_scheduled_crawl)}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {isActiveCrawling && (
                            <div className="flex items-center gap-2 px-3 py-1 bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 rounded-lg">
                              <RefreshCw className="w-4 h-4 animate-spin" />
                              <span className="text-sm font-medium">Crawling...</span>
                            </div>
                          )}
                          {isCompleted && !isActiveCrawling && (
                            <div className="flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 rounded-lg">
                              <CheckCircle2 className="w-4 h-4" />
                              <span className="text-sm font-medium">Done</span>
                            </div>
                          )}
                          {hasError && (
                            <div className="flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 rounded-lg">
                              <XCircle className="w-4 h-4" />
                              <span className="text-sm font-medium">Error</span>
                            </div>
                          )}
                          {!isActiveCrawling && !status && (
                            <button
                              onClick={() => triggerCrawl(config.site_name, config.base_url)}
                              className="px-4 py-2 bg-primary-600 dark:bg-primary-500 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors text-sm font-medium"
                            >
                              Crawl Now
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {inactiveConfigs.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3 uppercase tracking-wide">
                Inactive Sites ({inactiveConfigs.length})
              </h3>
              <div className="grid gap-4">
                {inactiveConfigs.map((config) => (
                  <div
                    key={config.id}
                    className="border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 opacity-60"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-3 h-3 bg-gray-400 dark:bg-gray-600 rounded-full"></div>
                      <h4 className="text-lg font-semibold text-gray-600 dark:text-gray-400">
                        {config.site_name}
                      </h4>
                      <span className="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs font-medium rounded">
                        Inactive
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-500 truncate">{config.base_url}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ActiveCrawls;

